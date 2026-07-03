"""Score CPLD control-extraction architectures (74HC glue + optional Flash CW)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from alu_decode_arch import pack_dips, score_hc154, sop_parts_from_decode
from alu_decode_cost import DecodeCost
from alu_decode_model import (
    PROFILE_LGC_DIRECT,
    build_table,
    default_lgc_direct_arith,
    merge_lgc_direct,
)

from cpld_ctrl_model import (
    IDX5_SLOTS,
    active_idx4_slots,
    active_idx5_slots,
    alu_truth_table,
    build_v10_ctrl_table,
    strobe_truth_table,
)
from flash_cw_timing import EXEC_HALF_NS, budget_for_arch

DELAY_SUB_DATAPATH = 136
DELAY_ALU_INC = 153
DELAY_ALU_CMP_SUB_MODEL = 151
DELAY_SUB_WITH_DECODE = DELAY_SUB_DATAPATH
DELAY_DECODE_SAVED = 15
DELAY_EXT_CTRL_PENALTY = 8
DELAY_CW16_DIRECT = DELAY_SUB_DATAPATH

GPR_ONLY_MC = 26
BASELINE_MC = 38
ATF1504_MC_LIMIT = 64

WIRE_HOPS_BASELINE = 118
WIRE_HOPS_EXT_CTRL = 128
WIRE_HOPS_FLASH_CW = 122

DECODE_SOP_DIP = 9
FLASH_ROWS_IDX4 = 26
FLASH_ROWS_IDX5 = 26

ARCH_BASELINE_FSM = "baseline_fsm"
ARCH_FLASH_CW10 = "flash_cw10_decode"
ARCH_FLASH_CW16 = "flash_cw16_direct"
ARCH_SOP_IDX5 = "sop_idx5"
ARCH_HC154_LAYERED = "hc154_layered"
ARCH_COUNTER_TEMPLATE = "counter_template"
ARCH_SPLIT_ALU_SEQ = "split_alu_seq"

CONTROL_ARCHITECTURES = (
    ARCH_BASELINE_FSM,
    ARCH_FLASH_CW10,
    ARCH_FLASH_CW16,
    ARCH_SOP_IDX5,
    ARCH_HC154_LAYERED,
    ARCH_COUNTER_TEMPLATE,
    ARCH_SPLIT_ALU_SEQ,
)

PURE_74HC_ARCHITECTURES = frozenset(
    {ARCH_SOP_IDX5, ARCH_HC154_LAYERED, ARCH_COUNTER_TEMPLATE, ARCH_SPLIT_ALU_SEQ}
)


class IndexWidth(str, Enum):
    IDX4 = "idx4"
    IDX5 = "idx5"


@dataclass(frozen=True)
class CtrlArchCost:
    arch: str
    index_width: IndexWidth
    dip_74hc: int
    delay_max_ns: int
    flash_rows: int
    cpld_mc: int
    wire_hops: int
    gates: int
    advanced_blocks: int
    parts: dict[str, int] = field(default_factory=dict)
    feasible: bool = True
    pure_74hc: bool = False
    notes: list[str] = field(default_factory=list)
    delay_alu_ns: int = 0
    delay_fetch_ns: int = 0
    delay_execute_ns: int = 0
    timing_feasible: bool = True

    @property
    def key(self) -> str:
        return f"{self.arch}_{self.index_width.value}"

    def pareto_key(self) -> tuple[int, int, int]:
        return (self.dip_74hc, self.delay_max_ns, self.flash_rows)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "arch": self.arch,
            "index_width": self.index_width.value,
            "dip_74hc": self.dip_74hc,
            "delay_max_ns": self.delay_max_ns,
            "delay_alu_ns": self.delay_alu_ns,
            "delay_fetch_ns": self.delay_fetch_ns,
            "delay_execute_ns": self.delay_execute_ns,
            "timing_feasible": self.timing_feasible,
            "flash_rows": self.flash_rows,
            "cpld_mc": self.cpld_mc,
            "wire_hops": self.wire_hops,
            "gates": self.gates,
            "advanced_blocks": self.advanced_blocks,
            "parts": dict(self.parts),
            "feasible": self.feasible,
            "pure_74hc": self.pure_74hc,
            "notes": list(self.notes),
        }


class _IdxGateCounter:
    """SOP gate count for 7-bit idx5 address lines."""

    def __init__(self, addr_bits: int = 7) -> None:
        self.addr_bits = addr_bits
        self.n04 = 0
        self.n08 = 0
        self.n32 = 0
        self._internal = 0

    def cost(self) -> DecodeCost:
        return DecodeCost(self.n04, self.n08, self.n32)

    def _fresh(self) -> str:
        self._internal += 1
        return f"_t{self._internal}"

    def _new04(self) -> None:
        self.n04 += 1

    def _new08(self) -> None:
        self.n08 += 1

    def _new32(self) -> None:
        self.n32 += 1

    def _literal(self, bit: int, val: int) -> str:
        if val == 1:
            return f"i{bit}"
        self._new04()
        return self._fresh()

    def _and(self, a: str, b: str) -> str:
        if a == "gnd" or b == "gnd":
            return "gnd"
        if a == "vcc":
            return b
        if b == "vcc":
            return a
        self._new08()
        return self._fresh()

    def _and_many(self, terms: list[str]) -> str:
        cur = terms[0]
        for t in terms[1:]:
            cur = self._and(cur, t)
        return cur

    def _or(self, a: str, b: str) -> str:
        if a == "gnd":
            return b
        if b == "gnd":
            return a
        self._new32()
        return self._fresh()

    def _or_many(self, terms: list[str]) -> str:
        cur = terms[0]
        for t in terms[1:]:
            cur = self._or(cur, t)
        return cur

    def _match_idx(self, idx: int) -> str:
        terms: list[str] = []
        for bit in range(self.addr_bits):
            terms.append(self._literal(bit, (idx >> bit) & 1))
        return self._and_many(terms)

    def _buf(self) -> None:
        self._new08()


def score_idx_sop(
    table: list[dict[str, int]],
    outputs: list[str],
    *,
    addr_bits: int = 7,
    slot_count: int = IDX5_SLOTS,
) -> DecodeCost:
    by_idx = {int(r["idx"]): r for r in table}
    if len(by_idx) != slot_count:
        raise ValueError(f"expected {slot_count} idx rows, got {len(by_idx)}")

    gc = _IdxGateCounter(addr_bits)
    for sig in outputs:
        active = [idx for idx in range(slot_count) if int(by_idx[idx].get(sig, 0)) == 1]
        if active:
            gc._or_many([gc._match_idx(idx) for idx in active])
            gc._buf()
        else:
            gc._buf()
    return gc.cost()


def _alu_decode_rows() -> tuple[list[dict], int | None]:
    assign = merge_lgc_direct(default_lgc_direct_arith())
    return build_table(assign, PROFILE_LGC_DIRECT)


def _sum_decode_costs(*costs: DecodeCost) -> tuple[int, dict[str, int], int]:
    total_gates = sum(c.total for c in costs)
    parts: dict[str, int] = {}
    for c in costs:
        for part, n in sop_parts_from_decode(c).items():
            parts[part] = parts.get(part, 0) + n
    return total_gates, parts, pack_dips(parts)


def _strobe_outputs() -> list[str]:
    return [
        "reg_we",
        "mem_rd",
        "mem_wr",
        "y_oe",
        "w_sel0",
        "w_sel1",
        "xfer_src0",
        "xfer_src1",
        "pc_load_en",
    ]


def _alu_outputs() -> list[str]:
    return [
        "cin",
        "bctrl0",
        "bctrl1",
        "bctrl2",
        "bctrl3",
        "lgc0",
        "lgc1",
        "lgc2",
        "lgc3",
        "y_mux_sel",
    ]


def _branch_glue_dip() -> int:
    return 1


def _counter_template_parts() -> dict[str, int]:
    return {
        "74HC161": 1,
        "74HC08": 6,
        "74HC32": 4,
        "74HC153": 2,
        "74HC138": 1,
        "74HC574": 1,
    }


_E2E_TIMING_ARCHS = frozenset(
    {ARCH_BASELINE_FSM, ARCH_FLASH_CW10, ARCH_FLASH_CW16}
)


def _timing_bundle(arch: str, fallback_alu_ns: int) -> dict:
    """Return delay_* fields and timing notes for CtrlArchCost."""
    if arch in _E2E_TIMING_ARCHS:
        b = budget_for_arch(arch)
        notes: list[str] = []
        if arch in (ARCH_FLASH_CW10, ARCH_FLASH_CW16) and not b.serial_ok:
            notes.append(
                f"serial same-half {b.serial_total_ns} ns > {EXEC_HALF_NS}; pipelined CW fetch required"
            )
        return {
            "delay_alu_ns": b.delay_alu_ns,
            "delay_fetch_ns": b.delay_fetch_ns,
            "delay_execute_ns": b.delay_execute_ns,
            "delay_max_ns": b.delay_execute_ns,
            "timing_feasible": b.pipelined_ok,
            "timing_notes": notes,
        }
    if arch == ARCH_HC154_LAYERED:
        execute = DELAY_SUB_WITH_DECODE
    elif arch == ARCH_SPLIT_ALU_SEQ:
        execute = DELAY_SUB_WITH_DECODE
    elif arch in PURE_74HC_ARCHITECTURES:
        execute = fallback_alu_ns + DELAY_EXT_CTRL_PENALTY
    else:
        execute = fallback_alu_ns
    return {
        "delay_alu_ns": fallback_alu_ns,
        "delay_fetch_ns": 0,
        "delay_execute_ns": execute,
        "delay_max_ns": execute,
        "timing_feasible": execute <= EXEC_HALF_NS,
        "timing_notes": [],
    }


def _merge_notes(*parts: list[str]) -> list[str]:
    out: list[str] = []
    for p in parts:
        for n in p:
            if n not in out:
                out.append(n)
    return out


def score_control_arch(arch: str, index_width: IndexWidth) -> CtrlArchCost:
    rows = build_v10_ctrl_table()
    idx_key = index_width.value
    addr_bits = 7 if index_width == IndexWidth.IDX5 else 6
    slot_count = 128 if index_width == IndexWidth.IDX5 else 64
    flash_rows = FLASH_ROWS_IDX5 if index_width == IndexWidth.IDX5 else FLASH_ROWS_IDX4

    if arch == ARCH_BASELINE_FSM:
        timing = _timing_bundle(arch, DELAY_CW16_DIRECT)
        mc_ok = BASELINE_MC <= ATF1504_MC_LIMIT
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=0,
            flash_rows=0,
            cpld_mc=BASELINE_MC,
            wire_hops=WIRE_HOPS_BASELINE,
            gates=0,
            advanced_blocks=1,
            parts={"ATF1504": 1},
            feasible=mc_ok and timing["timing_feasible"],
            pure_74hc=False,
            notes=_merge_notes(["normative v1.0: GPR + idx5 FSM in CPLD"], timing["timing_notes"]),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    if arch == ARCH_FLASH_CW10:
        dip = 1 + DECODE_SOP_DIP + 2
        timing = _timing_bundle(arch, DELAY_SUB_WITH_DECODE)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=flash_rows,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_FLASH_CW,
            gates=0,
            advanced_blocks=0,
            parts={"74HC574": 1},
            feasible=timing["timing_feasible"],
            pure_74hc=False,
            notes=_merge_notes(
                ["Flash $4000 + 574 CW latch + alu8_decode SOP"],
                timing["timing_notes"],
            ),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    if arch == ARCH_FLASH_CW16:
        dip = 3
        if index_width == IndexWidth.IDX5:
            dip += 1
        timing = _timing_bundle(arch, DELAY_CW16_DIRECT)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=flash_rows,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_FLASH_CW,
            gates=0,
            advanced_blocks=0,
            parts={"74HC574": 2},
            feasible=timing["timing_feasible"],
            pure_74hc=False,
            notes=_merge_notes(
                ["16b CW direct to ALU/bus; no alu8_decode"],
                timing["timing_notes"],
            ),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    strobe_tbl = strobe_truth_table(idx_key=idx_key)
    alu_tbl = alu_truth_table(rows, idx_key=idx_key)
    strobe_cost = score_idx_sop(
        strobe_tbl, _strobe_outputs(), addr_bits=addr_bits, slot_count=slot_count
    )
    alu_cost = score_idx_sop(
        alu_tbl, _alu_outputs(), addr_bits=addr_bits, slot_count=slot_count
    )

    if arch == ARCH_SOP_IDX5:
        gates, parts, dip = _sum_decode_costs(strobe_cost, alu_cost)
        dip += 2 + _branch_glue_dip()
        feasible = dip <= 80 and gates <= 600
        active = (
            len(active_idx5_slots(rows))
            if index_width == IndexWidth.IDX5
            else len(active_idx4_slots(rows))
        )
        notes = [
            f"idx{addr_bits} SOP strobes+ALU: {strobe_cost} + {alu_cost}",
            f"active slots: {active}",
        ]
        if not feasible:
            notes.append("SOP gate/DIP explosion — research only")
        timing = _timing_bundle(arch, DELAY_CW16_DIRECT)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates,
            advanced_blocks=0,
            parts=parts,
            feasible=feasible and timing["timing_feasible"],
            pure_74hc=True,
            notes=_merge_notes(notes, timing["timing_notes"]),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    if arch == ARCH_HC154_LAYERED:
        alu_rows, cmp_op = _alu_decode_rows()
        alu_dec = score_hc154(alu_rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
        gates, parts, _dip_seq = _sum_decode_costs(strobe_cost)
        parts = dict(parts)
        for k, v in alu_dec.parts.items():
            parts[k] = parts.get(k, 0) + v
        dip = pack_dips(parts) + 2 + _branch_glue_dip()
        timing = _timing_bundle(arch, DELAY_SUB_WITH_DECODE)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates + alu_dec.gates,
            advanced_blocks=alu_dec.advanced_blocks,
            parts=parts,
            feasible=timing["timing_feasible"],
            pure_74hc=True,
            notes=_merge_notes(
                ["strobes: idx SOP; ALU: 74HC154+00 from 4b alu_op field"] + alu_dec.notes[:2],
                timing["timing_notes"],
            ),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    if arch == ARCH_COUNTER_TEMPLATE:
        parts = _counter_template_parts()
        dip = pack_dips(parts) + _branch_glue_dip()
        timing = _timing_bundle(arch, DELAY_CW16_DIRECT)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL - 4,
            gates=strobe_cost.total // 3,
            advanced_blocks=0,
            parts=parts,
            feasible=timing["timing_feasible"],
            pure_74hc=True,
            notes=_merge_notes(
                [
                    "161 phase counter + opcode→template glue + 153 w_sel",
                    f"template strobes est. {strobe_cost.total} gates if fully SOP",
                ],
                timing["timing_notes"],
            ),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    if arch == ARCH_SPLIT_ALU_SEQ:
        gates, parts, dip_seq = _sum_decode_costs(strobe_cost)
        dip = dip_seq + DECODE_SOP_DIP + 2 + _branch_glue_dip()
        timing = _timing_bundle(arch, DELAY_SUB_WITH_DECODE)
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates,
            advanced_blocks=0,
            parts=parts,
            feasible=timing["timing_feasible"],
            pure_74hc=True,
            notes=_merge_notes(
                ["idx SOP sequencer + separate alu8_decode SOP block"],
                timing["timing_notes"],
            ),
            delay_alu_ns=timing["delay_alu_ns"],
            delay_fetch_ns=timing["delay_fetch_ns"],
            delay_execute_ns=timing["delay_execute_ns"],
            delay_max_ns=timing["delay_max_ns"],
            timing_feasible=timing["timing_feasible"],
        )

    raise ValueError(f"unknown arch: {arch}")


def iter_control_configs(
    arches: tuple[str, ...] = CONTROL_ARCHITECTURES,
) -> list[tuple[str, IndexWidth]]:
    out: list[tuple[str, IndexWidth]] = []
    for arch in arches:
        if arch == ARCH_BASELINE_FSM:
            out.append((arch, IndexWidth.IDX5))
            continue
        if arch == ARCH_FLASH_CW10:
            out.append((arch, IndexWidth.IDX4))
            out.append((arch, IndexWidth.IDX5))
            continue
        for idx in IndexWidth:
            out.append((arch, idx))
    return out


def score_all_configs(
    arches: tuple[str, ...] = CONTROL_ARCHITECTURES,
) -> list[CtrlArchCost]:
    return [score_control_arch(arch, idx) for arch, idx in iter_control_configs(arches)]


def dominates(a: CtrlArchCost, b: CtrlArchCost) -> bool:
    if not a.feasible:
        return False
    if not b.feasible:
        return True
    ak, bk = a.pareto_key(), b.pareto_key()
    return ak <= bk and ak != bk


def pareto_front(costs: list[CtrlArchCost]) -> list[CtrlArchCost]:
    front: list[CtrlArchCost] = []
    for ca in costs:
        if not ca.feasible:
            continue
        if any(dominates(cb, ca) for cb in costs if cb.feasible and cb is not ca):
            continue
        front.append(ca)
    front.sort(key=lambda c: c.pareto_key())
    return front


def min_dip(costs: list[CtrlArchCost], *, pure_only: bool = False) -> CtrlArchCost | None:
    pool = [c for c in costs if c.feasible and (not pure_only or c.pure_74hc)]
    if not pool:
        return None
    return min(pool, key=lambda c: (c.dip_74hc, c.delay_max_ns, c.flash_rows))
