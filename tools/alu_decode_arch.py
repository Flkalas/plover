"""Decode implementation architectures: DIP / advanced-block cost beyond SOP gate count."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from alu_decode_cost import DecodeCost, score_truth_table
from alu_decode_model import (
    PROFILE_LGC_DIRECT,
    profile_options,
    profile_outputs,
)

ARCH_SOP = "sop"
ARCH_LGC_DIRECT = "lgc_direct"
ARCH_HC154 = "hc154"
ARCH_CW_DIRECT = "cw_direct"
ARCH_CPLD = "cpld"

ARCHITECTURES = (ARCH_SOP, ARCH_LGC_DIRECT, ARCH_HC154, ARCH_CW_DIRECT, ARCH_CPLD)

# ATF1504: ~40 MC total; GPR ~35 ??decode budget (parameterized).
DEFAULT_CPLD_MC_BUDGET = 5

# lgc_direct ALU-local glue (not in SOP decode count).
LGC_LOCAL_OR_GATES = 3


@dataclass(frozen=True)
class ArchCost:
    arch: str
    dips: int
    advanced_blocks: int
    gates: int
    parts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    feasible: bool = True

    def as_dict(self) -> dict:
        return {
            "arch": self.arch,
            "dips": self.dips,
            "advanced_blocks": self.advanced_blocks,
            "gates": self.gates,
            "parts": dict(self.parts),
            "notes": list(self.notes),
            "feasible": self.feasible,
        }

    def lex_key(self) -> tuple[int, int, int]:
        return (self.dips, self.advanced_blocks, self.gates)


def pack_dips(parts: dict[str, int]) -> int:
    """Sum DIP packages from part counts (gates per package)."""
    per_chip = {
        "74HC04": 6,
        "74HC08": 4,
        "74HC32": 4,
        "74HC00": 4,
        "74HC154": 1,
    }
    total = 0
    for part, count in parts.items():
        slots = per_chip.get(part, 1)
        total += (count + slots - 1) // slots if count > 0 else 0
    return total


def sop_parts_from_decode(cost: DecodeCost) -> dict[str, int]:
    return {
        "74HC04": cost.n04,
        "74HC08": cost.n08,
        "74HC32": cost.n32,
    }


def score_sop(
    rows: list[dict],
    profile: str,
    *,
    cmp_op: int | None,
) -> ArchCost:
    opts = profile_options(profile)
    outputs = profile_outputs(profile)
    dec = score_truth_table(rows, outputs, cmp_op=cmp_op, **opts)
    parts = sop_parts_from_decode(dec)
    dips = pack_dips(parts)
    return ArchCost(
        arch=ARCH_SOP,
        dips=dips,
        advanced_blocks=0,
        gates=dec.total,
        parts=parts,
        notes=[f"SOP {dec}"],
    )


def score_lgc_direct_sop(
    rows: list[dict],
    *,
    cmp_op: int | None,
) -> ArchCost:
    base = score_sop(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    parts = dict(base.parts)
    parts["74HC32"] = parts.get("74HC32", 0) + LGC_LOCAL_OR_GATES
    dips = pack_dips(parts)
    notes = list(base.notes) + [f"local y_mux OR x{LGC_LOCAL_OR_GATES}"]
    return ArchCost(
        arch=ARCH_LGC_DIRECT,
        dips=dips,
        advanced_blocks=0,
        gates=base.gates + LGC_LOCAL_OR_GATES,
        parts=parts,
        notes=notes,
    )


def _nand_tree_count(n_inputs: int) -> int:
    """2-input NAND tree: n active-low lines -> max(0, n-1) NAND gates."""
    if n_inputs <= 1:
        return 0
    return n_inputs - 1


def _active_ops(rows: list[dict], sig: str) -> list[int]:
    return [int(r["op"]) for r in rows if int(r.get(sig, 0)) == 1]


def score_hc154(
    rows: list[dict],
    profile: str,
    *,
    cmp_op: int | None,
) -> ArchCost:
    """74HC154 one-hot + 74HC00 NAND glue over active-low Y outputs."""
    opts = profile_options(profile)
    outputs = profile_outputs(profile)
    nand_gates = 0
    glue_notes: list[str] = []

    for sig in outputs:
        ops = _active_ops(rows, sig)
        n = _nand_tree_count(len(ops))
        nand_gates += n
        if ops:
            glue_notes.append(f"{sig}: NAND({len(ops)} Y) x{n}")

    if opts.get("include_cmp_n") and cmp_op is not None:
        glue_notes.append(f"cmp_n: Y{cmp_op} direct (0 NAND)")

    parts: dict[str, int] = {"74HC154": 1}
    if nand_gates:
        parts["74HC00"] = nand_gates

    dips = pack_dips(parts)
    # lgc_direct still needs local y_mux OR when not using CW
    if profile == PROFILE_LGC_DIRECT:
        parts = dict(parts)
        parts["74HC32"] = parts.get("74HC32", 0) + LGC_LOCAL_OR_GATES
        dips = pack_dips(parts)
        glue_notes.append(f"local y_mux OR x{LGC_LOCAL_OR_GATES}")

    return ArchCost(
        arch=ARCH_HC154,
        dips=dips,
        advanced_blocks=1,
        gates=nand_gates + (LGC_LOCAL_OR_GATES if profile == PROFILE_LGC_DIRECT else 0),
        parts=parts,
        notes=["74HC154 + NAND glue"] + glue_notes,
    )


def score_cw_direct(profile: str) -> ArchCost:
    return ArchCost(
        arch=ARCH_CW_DIRECT,
        dips=0,
        advanced_blocks=0,
        gates=0,
        parts={},
        notes=[
            "CW_L B7-B4 raw: cin, b_sel, b_const_sel, cmp_n (no comb decode)",
            "pack_control_store / microcode-spec breaking",
        ],
    )


def _estimate_product_terms(rows: list[dict], outputs: list[str], *, cmp_op: int | None) -> int:
    total = 0
    for sig in outputs:
        total += len(_active_ops(rows, sig))
    if cmp_op is not None:
        total += 1
    return total


def score_cpld(
    rows: list[dict],
    profile: str,
    *,
    cmp_op: int | None,
    mc_budget: int = DEFAULT_CPLD_MC_BUDGET,
) -> ArchCost:
    outputs = profile_outputs(profile)
    opts = profile_options(profile)
    n_in = 4
    n_out = len(outputs) + (1 if opts.get("include_cmp_n") else 0)
    pterms = _estimate_product_terms(rows, outputs, cmp_op=cmp_op if opts.get("include_cmp_n") else None)
    mc_est = n_in + n_out + pterms
    feasible = mc_est <= mc_budget
    notes = [
        f"est MC: in={n_in} out={n_out} pterms={pterms} total={mc_est} budget={mc_budget}",
    ]
    if not feasible:
        notes.append("exceeds CPLD MC budget")
    return ArchCost(
        arch=ARCH_CPLD,
        dips=0,
        advanced_blocks=1 if feasible else 0,
        gates=0,
        parts={"ATF1504": 1} if feasible else {},
        notes=notes,
        feasible=feasible,
    )


def score_architecture(
    arch: str,
    rows: list[dict],
    profile: str,
    *,
    cmp_op: int | None,
    mc_budget: int = DEFAULT_CPLD_MC_BUDGET,
) -> ArchCost:
    if arch == ARCH_SOP:
        return score_sop(rows, profile, cmp_op=cmp_op)
    if arch == ARCH_LGC_DIRECT:
        return score_lgc_direct_sop(rows, cmp_op=cmp_op)
    if arch == ARCH_HC154:
        return score_hc154(rows, profile, cmp_op=cmp_op)
    if arch == ARCH_CW_DIRECT:
        return score_cw_direct(profile)
    if arch == ARCH_CPLD:
        return score_cpld(rows, profile, cmp_op=cmp_op, mc_budget=mc_budget)
    raise ValueError(f"unknown arch: {arch}")


def score_all_architectures(
    rows: list[dict],
    profile: str,
    *,
    cmp_op: int | None,
    arches: tuple[str, ...] = ARCHITECTURES,
    mc_budget: int = DEFAULT_CPLD_MC_BUDGET,
) -> dict[str, ArchCost]:
    out: dict[str, ArchCost] = {}
    for arch in arches:
        out[arch] = score_architecture(arch, rows, profile, cmp_op=cmp_op, mc_budget=mc_budget)
    return out


def recommend_arch(costs: dict[str, ArchCost]) -> str:
    feasible = {k: v for k, v in costs.items() if v.feasible}
    if not feasible:
        return ARCH_SOP
    return min(feasible.keys(), key=lambda k: feasible[k].lex_key())


def dominates(a: ArchCost, b: ArchCost) -> bool:
    """True if a is <= b on all metrics and strictly better on at least one."""
    if not a.feasible:
        return False
    if not b.feasible:
        return True
    ak, bk = a.lex_key(), b.lex_key()
    return ak <= bk and ak != bk


def pareto_front(
    entries: list[tuple[str, str, ArchCost]],
) -> list[tuple[str, str, ArchCost]]:
    """Non-dominated (assignment_key, arch, cost) triples."""
    front: list[tuple[str, str, ArchCost]] = []
    for key_a, arch_a, cost_a in entries:
        if not cost_a.feasible:
            continue
        dominated_by_other = False
        for key_b, arch_b, cost_b in entries:
            if not cost_b.feasible:
                continue
            if dominates(cost_b, cost_a):
                dominated_by_other = True
                break
        if not dominated_by_other:
            front.append((key_a, arch_a, cost_a))
    front.sort(key=lambda x: x[2].lex_key())
    return front


def assignment_key(assignment: dict[str, int]) -> str:
    return ",".join(f"{k}={assignment[k]}" for k in sorted(assignment))


def arch_cost_to_sop_dips(cost: DecodeCost) -> int:
    return pack_dips(sop_parts_from_decode(cost))
