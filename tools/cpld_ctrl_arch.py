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

DELAY_SUB_WITH_DECODE = 151
DELAY_DECODE_SAVED = 15
DELAY_EXT_CTRL_PENALTY = 8
DELAY_CW16_DIRECT = DELAY_SUB_WITH_DECODE - DELAY_DECODE_SAVED

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
        "b_sel",
        "b_const_sel",
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


def score_control_arch(arch: str, index_width: IndexWidth) -> CtrlArchCost:
    rows = build_v10_ctrl_table()
    idx_key = index_width.value
    addr_bits = 7 if index_width == IndexWidth.IDX5 else 6
    slot_count = 128 if index_width == IndexWidth.IDX5 else 64
    flash_rows = FLASH_ROWS_IDX5 if index_width == IndexWidth.IDX5 else FLASH_ROWS_IDX4

    if arch == ARCH_BASELINE_FSM:
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=0,
            delay_max_ns=DELAY_CW16_DIRECT + 5,
            flash_rows=0,
            cpld_mc=BASELINE_MC,
            wire_hops=WIRE_HOPS_BASELINE,
            gates=0,
            advanced_blocks=1,
            parts={"ATF1504": 1},
            feasible=BASELINE_MC <= ATF1504_MC_LIMIT,
            pure_74hc=False,
            notes=["normative v1.0: GPR + idx5 FSM in CPLD"],
        )

    if arch == ARCH_FLASH_CW10:
        dip = 1 + DECODE_SOP_DIP + 2
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_SUB_WITH_DECODE,
            flash_rows=flash_rows,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_FLASH_CW,
            gates=0,
            advanced_blocks=0,
            parts={"74HC574": 1},
            feasible=True,
            pure_74hc=False,
            notes=["Flash $4000 + 574 CW latch + alu8_decode SOP"],
        )

    if arch == ARCH_FLASH_CW16:
        dip = 3
        if index_width == IndexWidth.IDX5:
            dip += 1
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_CW16_DIRECT,
            flash_rows=flash_rows,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_FLASH_CW,
            gates=0,
            advanced_blocks=0,
            parts={"74HC574": 2},
            feasible=True,
            pure_74hc=False,
            notes=["16b CW direct to ALU/bus; no alu8_decode"],
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
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_CW16_DIRECT + DELAY_EXT_CTRL_PENALTY,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates,
            advanced_blocks=0,
            parts=parts,
            feasible=feasible,
            pure_74hc=True,
            notes=notes,
        )

    if arch == ARCH_HC154_LAYERED:
        alu_rows, cmp_op = _alu_decode_rows()
        alu_dec = score_hc154(alu_rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
        gates, parts, _dip_seq = _sum_decode_costs(strobe_cost)
        parts = dict(parts)
        for k, v in alu_dec.parts.items():
            parts[k] = parts.get(k, 0) + v
        dip = pack_dips(parts) + 2 + _branch_glue_dip()
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_SUB_WITH_DECODE,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates + alu_dec.gates,
            advanced_blocks=alu_dec.advanced_blocks,
            parts=parts,
            feasible=True,
            pure_74hc=True,
            notes=["strobes: idx SOP; ALU: 74HC154+00 from 4b alu_op field"]
            + alu_dec.notes[:2],
        )

    if arch == ARCH_COUNTER_TEMPLATE:
        parts = _counter_template_parts()
        dip = pack_dips(parts) + _branch_glue_dip()
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_CW16_DIRECT + DELAY_EXT_CTRL_PENALTY,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL - 4,
            gates=strobe_cost.total // 3,
            advanced_blocks=0,
            parts=parts,
            feasible=True,
            pure_74hc=True,
            notes=[
                "161 phase counter + opcode→template glue + 153 w_sel",
                f"template strobes est. {strobe_cost.total} gates if fully SOP",
            ],
        )

    if arch == ARCH_SPLIT_ALU_SEQ:
        gates, parts, dip_seq = _sum_decode_costs(strobe_cost)
        dip = dip_seq + DECODE_SOP_DIP + 2 + _branch_glue_dip()
        return CtrlArchCost(
            arch=arch,
            index_width=index_width,
            dip_74hc=dip,
            delay_max_ns=DELAY_SUB_WITH_DECODE,
            flash_rows=0,
            cpld_mc=GPR_ONLY_MC,
            wire_hops=WIRE_HOPS_EXT_CTRL,
            gates=gates,
            advanced_blocks=0,
            parts=parts,
            feasible=True,
            pure_74hc=True,
            notes=["idx SOP sequencer + separate alu8_decode SOP block"],
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
