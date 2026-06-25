"""CPU 4-axis architecture cost model (opcode / decode / CPLD / CW-Flash).

Used by cpu_arch_search.py for Pareto ranking: DIP, delay, flash_rows, MC, hops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

# --- Axis enums ----------------------------------------------------------------

class OpEncoding(str, Enum):
    OP_LEGACY = "op_legacy"
    OP_EXPANDED = "op_expanded"
    OP_CLASS = "op_class"


class IndexWidth(str, Enum):
    IDX4 = "idx4"  # Pareto search winner (Flash archive / hybrid study)
    IDX5 = "idx5"  # Normative post-refinement: CPLD FSM (opcode[4:0]<<2)|phase
    IDX8 = "idx8"
    IDX_CLASS = "idx_class"


class DecodeSplit(str, Enum):
    DEC_SOP = "dec_sop"
    DEC_HC154 = "dec_hc154"
    DEC_CW_DIRECT = "dec_cw_direct"
    DEC_CPLD_SEQ = "dec_cpld_seq"


class CpldMode(str, Enum):
    CPLD_4GPR = "cpld_4gpr"
    CPLD_3FIXED = "cpld_3fixed"
    CPLD_3SEQ = "cpld_3seq"
    EXT_574X3 = "ext_574x3"


class CwFlashMode(str, Enum):
    CW10_ALUOP = "cw10_aluop"
    CW16_DIRECT = "cw16_direct"
    CW8_PARAM = "cw8_param"
    CW_HYBRID = "cw_hybrid"


# v1.0 packed macro opcodes (pack_control_store.sequences phase counts)
LEGACY_PHASES: dict[int, int] = {
    0x01: 3,  # ADD
    0x02: 2,  # LDA
    0x03: 2,  # STA
    0x04: 2,  # BEQ
    0x05: 1,  # JMP
    0x06: 1,  # CALL (planned)
    0x07: 1,  # RET
    0x08: 2,  # LDIO
    0x09: 2,  # STIO
    0x0A: 1,  # HALT
    0x0D: 3,  # CMP
    0x0F: 2,  # STA16
    0x10: 1,  # TFR01
    0x11: 1,  # TFR02
    0x12: 1,  # TFR10
    0x13: 1,  # TFR12
    0x14: 1,  # TFR20
    0x15: 1,  # TFR21
}

# Expanded ISA representative opcode counts (interpreter + PL-DOS draft)
EXPANDED_OPCODE_COUNT = 64  # 0x10-0x4F active stubs
EXPANDED_AVG_PHASES = 2.2

# Opcode class families (upper nibble) for op_class + idx_class
CLASS_COUNT = 16
CLASS_PHASES = 4  # max phases per family template

# CPLD sequencer: these macros need no per-phase Flash rows (FSM template)
# Extended group 0x10–0x1F (TFR 0x10–0x15 + reserved) uses idx5 CPLD slots only.
CPLD_SEQUENCED_OPS = frozenset(
    {0x01, 0x02, 0x03, 0x08, 0x09, 0x0D, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x20, 0x21}
)

# Post-refinement idx5: extra K-map vs Pareto idx4 (~26–32 → ~38 MC)
IDX5_EXTRA_MC = 6

# Flash param row per opcode when hybrid / cw8_param
PARAM_ROW_PER_OPCODE = 1

ATF1504_MC_LIMIT = 64

# Breadboard 74HC DIP baseline (v1.0 normative, includes alu_decode in ALU area)
BASE_DIP_V10 = 31

# Decode block DIP (alu_decode SOP — see archive/pre-v1.1b/alu-decode-architecture-study.md)
DECODE_DIP: dict[DecodeSplit, int] = {
    DecodeSplit.DEC_SOP: 9,
    DecodeSplit.DEC_HC154: 3,
    DecodeSplit.DEC_CW_DIRECT: 0,
    DecodeSplit.DEC_CPLD_SEQ: 0,
}

# Critical-path SUB delay @ 74HC max (ns) — alu-opcodes-timing / alu_b3_sub_critical
DELAY_SUB_WITH_DECODE = 151
DELAY_DECODE_SAVED = 15  # control nets bypass alu_decode
DELAY_CPLD_SEQ_PENALTY = 5  # registered CPLD ctrl vs comb CW

# BEQ glue: partial 08/32 on breadboard
BEQ_GLUE_DIP = 1
BEQ_GLUE_DIP_CPLD_SEQ = 0

# idx8 CW address mux widen
IDX8_EXTRA_DIP = 1

# hybrid: one fewer 574 CW latch
CW_HYBRID_574_SAVED = 1

# ext 574x3: +3 574, no CPLD (CPLD not in 74HC count)
EXT_574_EXTRA = 3

# Parasitics wire_hops by variant key (from estimate_parasitics.py)
WIRE_HOPS: dict[str, int] = {
    "v1_breadboard": 125,
    "cpld_3fixed_cw_direct": 118,
    "cpld_3seq_hybrid": 115,
    "ext_574x3": 140,
}


@dataclass(frozen=True)
class CpuArchConfig:
    op_encoding: OpEncoding
    index_width: IndexWidth
    decode_split: DecodeSplit
    cpld_mode: CpldMode
    cw_flash: CwFlashMode

    @property
    def key(self) -> str:
        return "_".join(
            [
                self.op_encoding.value,
                self.index_width.value,
                self.decode_split.value,
                self.cpld_mode.value,
                self.cw_flash.value,
            ]
        )


@dataclass
class CpuArchCost:
    config: CpuArchConfig
    dip_74hc: int
    delay_max_ns: int
    flash_rows: int
    cpld_mc: int
    wire_hops: int
    feasible: bool
    notes: list[str] = field(default_factory=list)

    def pareto_key(self) -> tuple[int, int, int]:
        return (self.dip_74hc, self.delay_max_ns, self.flash_rows)

    def as_dict(self) -> dict:
        return {
            "key": self.config.key,
            "op_encoding": self.config.op_encoding.value,
            "index_width": self.config.index_width.value,
            "decode_split": self.config.decode_split.value,
            "cpld_mode": self.config.cpld_mode.value,
            "cw_flash": self.config.cw_flash.value,
            "dip_74hc": self.dip_74hc,
            "delay_max_ns": self.delay_max_ns,
            "flash_rows": self.flash_rows,
            "cpld_mc": self.cpld_mc,
            "wire_hops": self.wire_hops,
            "feasible": self.feasible,
            "notes": self.notes,
        }


def _legacy_flash_rows_per_phase() -> int:
    return sum(LEGACY_PHASES.values())


def _expanded_opcode_count(enc: OpEncoding) -> int:
    if enc == OpEncoding.OP_LEGACY:
        return len(LEGACY_PHASES)
    if enc == OpEncoding.OP_EXPANDED:
        return EXPANDED_OPCODE_COUNT
    return CLASS_COUNT * 4  # class variants


def flash_rows(
    enc: OpEncoding,
    idx: IndexWidth,
    decode: DecodeSplit,
    cw: CwFlashMode,
) -> int:
    """Estimate non-zero CW store rows used."""
    branch_rows = 12  # JMP/BEQ/CALL/RET/HALT/STA16 glue

    if cw == CwFlashMode.CW_HYBRID and decode == DecodeSplit.DEC_CPLD_SEQ:
        if enc == OpEncoding.OP_CLASS:
            return CLASS_COUNT + branch_rows
        if enc == OpEncoding.OP_LEGACY:
            return len(LEGACY_PHASES) + branch_rows
        # expanded: half sequenced — one param row each
        n_ops = EXPANDED_OPCODE_COUNT
        return n_ops + branch_rows

    if cw == CwFlashMode.CW8_PARAM and decode == DecodeSplit.DEC_CPLD_SEQ:
        return _expanded_opcode_count(enc) + branch_rows

    if enc == OpEncoding.OP_LEGACY and idx == IndexWidth.IDX4:
        if cw == CwFlashMode.CW10_ALUOP:
            return _legacy_flash_rows_per_phase()
        return len(LEGACY_PHASES) + branch_rows

    # Normative v1.0: idx5 FSM-only — no Flash CW rows
    if idx == IndexWidth.IDX5 and decode == DecodeSplit.DEC_CPLD_SEQ:
        return 0

    if idx == IndexWidth.IDX8:
        n = _expanded_opcode_count(enc)
        if cw == CwFlashMode.CW16_DIRECT:
            return int(n * EXPANDED_AVG_PHASES)
        return int(n * 2.0)  # cw10 per-phase

    if idx == IndexWidth.IDX_CLASS:
        return CLASS_COUNT * CLASS_PHASES + CLASS_COUNT

    return _legacy_flash_rows_per_phase()


def cpld_mc_estimate(mode: CpldMode, decode: DecodeSplit, idx: IndexWidth = IndexWidth.IDX4) -> int:
    base = {
        CpldMode.CPLD_4GPR: 40,
        CpldMode.CPLD_3FIXED: 26,
        CpldMode.CPLD_3SEQ: 44,
        CpldMode.EXT_574X3: 0,
    }[mode]
    if decode == DecodeSplit.DEC_CPLD_SEQ and mode == CpldMode.CPLD_3SEQ:
        base += 6  # branch sample + MEM gate
    if idx == IndexWidth.IDX5 and decode == DecodeSplit.DEC_CPLD_SEQ:
        base += IDX5_EXTRA_MC  # TFR 0x10–0x15 + opcode[4] decode
    if mode == CpldMode.EXT_574X3:
        return 0
    return base


def delay_max_ns(decode: DecodeSplit, cpld: CpldMode) -> int:
    if decode in (DecodeSplit.DEC_CW_DIRECT, DecodeSplit.DEC_CPLD_SEQ):
        d = DELAY_SUB_WITH_DECODE - DELAY_DECODE_SAVED
    else:
        d = DELAY_SUB_WITH_DECODE
    if decode == DecodeSplit.DEC_CPLD_SEQ and cpld == CpldMode.CPLD_3SEQ:
        d += DELAY_CPLD_SEQ_PENALTY
    return d


def dip_74hc_estimate(
    decode: DecodeSplit,
    cpld: CpldMode,
    idx: IndexWidth,
    cw: CwFlashMode,
) -> int:
    dip = BASE_DIP_V10 - DECODE_DIP[DecodeSplit.DEC_SOP] + DECODE_DIP[decode]

    if decode == DecodeSplit.DEC_CPLD_SEQ:
        dip -= BEQ_GLUE_DIP
    elif decode == DecodeSplit.DEC_CW_DIRECT:
        dip -= BEQ_GLUE_DIP - BEQ_GLUE_DIP_CPLD_SEQ

    if idx == IndexWidth.IDX8:
        dip += IDX8_EXTRA_DIP

    if cw == CwFlashMode.CW_HYBRID and decode == DecodeSplit.DEC_CPLD_SEQ:
        dip -= CW_HYBRID_574_SAVED

    if cpld == CpldMode.EXT_574X3:
        dip += EXT_574_EXTRA

    if cpld == CpldMode.CPLD_3FIXED and decode == DecodeSplit.DEC_CW_DIRECT:
        pass  # same DIP count as 4gpr (CPLD still present)

    return max(dip, 18)


def wire_hops_estimate(cpld: CpldMode, decode: DecodeSplit, cw: CwFlashMode) -> int:
    if cpld == CpldMode.EXT_574X3:
        return WIRE_HOPS["ext_574x3"]
    if cpld == CpldMode.CPLD_3SEQ and cw == CwFlashMode.CW_HYBRID:
        return WIRE_HOPS["cpld_3seq_hybrid"]
    if decode in (DecodeSplit.DEC_CW_DIRECT, DecodeSplit.DEC_CPLD_SEQ):
        return WIRE_HOPS["cpld_3fixed_cw_direct"]
    return WIRE_HOPS["v1_breadboard"]


def is_compatible(config: CpuArchConfig) -> bool:
    """Prune invalid axis combinations."""
    if config.cw_flash == CwFlashMode.CW_HYBRID and config.decode_split not in (
        DecodeSplit.DEC_CPLD_SEQ,
    ):
        return False
    if config.cw_flash == CwFlashMode.CW8_PARAM and config.decode_split != DecodeSplit.DEC_CPLD_SEQ:
        return False
    if config.decode_split == DecodeSplit.DEC_CPLD_SEQ and config.cpld_mode not in (
        CpldMode.CPLD_3SEQ,
        CpldMode.CPLD_3FIXED,
    ):
        return False
    if config.cpld_mode == CpldMode.EXT_574X3 and config.decode_split == DecodeSplit.DEC_CPLD_SEQ:
        return False
    if config.index_width == IndexWidth.IDX_CLASS and config.op_encoding != OpEncoding.OP_CLASS:
        return False
    if config.op_encoding == OpEncoding.OP_CLASS and config.index_width != IndexWidth.IDX_CLASS:
        return False
    if config.cw_flash == CwFlashMode.CW10_ALUOP and config.decode_split in (
        DecodeSplit.DEC_CW_DIRECT,
        DecodeSplit.DEC_CPLD_SEQ,
    ):
        return False
    if config.cw_flash in (CwFlashMode.CW16_DIRECT, CwFlashMode.CW8_PARAM) and config.decode_split == DecodeSplit.DEC_SOP:
        return False
    return True


def score_config(config: CpuArchConfig) -> CpuArchCost:
    mc = cpld_mc_estimate(config.cpld_mode, config.decode_split, config.index_width)
    rows = flash_rows(
        config.op_encoding,
        config.index_width,
        config.decode_split,
        config.cw_flash,
    )
    dip = dip_74hc_estimate(
        config.decode_split,
        config.cpld_mode,
        config.index_width,
        config.cw_flash,
    )
    delay = delay_max_ns(config.decode_split, config.cpld_mode)
    hops = wire_hops_estimate(config.cpld_mode, config.decode_split, config.cw_flash)
    feasible = mc <= ATF1504_MC_LIMIT and delay <= 250
    if config.cpld_mode == CpldMode.EXT_574X3:
        feasible = feasible and delay <= 250

    notes: list[str] = []
    if mc > ATF1504_MC_LIMIT:
        notes.append(f"CPLD MC {mc} > {ATF1504_MC_LIMIT}")
        feasible = False
    if config.decode_split == DecodeSplit.DEC_CPLD_SEQ:
        notes.append("phase FSM in CPLD; FSM-only opcode table (no Flash param)")
    if config.decode_split == DecodeSplit.DEC_CW_DIRECT:
        notes.append("no alu_decode DIP")

    return CpuArchCost(
        config=config,
        dip_74hc=dip,
        delay_max_ns=delay,
        flash_rows=rows,
        cpld_mc=mc,
        wire_hops=hops,
        feasible=feasible,
        notes=notes,
    )


def iter_configs() -> Iterator[CpuArchConfig]:
    for op in OpEncoding:
        for idx in IndexWidth:
            for dec in DecodeSplit:
                for cpld in CpldMode:
                    for cw in CwFlashMode:
                        cfg = CpuArchConfig(op, idx, dec, cpld, cw)
                        if is_compatible(cfg):
                            yield cfg


def baseline_v10_config() -> CpuArchConfig:
    return CpuArchConfig(
        OpEncoding.OP_LEGACY,
        IndexWidth.IDX4,
        DecodeSplit.DEC_SOP,
        CpldMode.CPLD_4GPR,
        CwFlashMode.CW10_ALUOP,
    )


def corner_h1_config() -> CpuArchConfig:
    return CpuArchConfig(
        OpEncoding.OP_CLASS,
        IndexWidth.IDX_CLASS,
        DecodeSplit.DEC_CPLD_SEQ,
        CpldMode.CPLD_3SEQ,
        CwFlashMode.CW_HYBRID,
    )


def corner_h2_config() -> CpuArchConfig:
    return CpuArchConfig(
        OpEncoding.OP_EXPANDED,
        IndexWidth.IDX8,
        DecodeSplit.DEC_CW_DIRECT,
        CpldMode.CPLD_3FIXED,
        CwFlashMode.CW16_DIRECT,
    )


def dominates(a: CpuArchCost, b: CpuArchCost) -> bool:
    if not a.feasible:
        return False
    if not b.feasible:
        return True
    ak, bk = a.pareto_key(), b.pareto_key()
    return ak <= bk and ak != bk


def pareto_front(costs: list[CpuArchCost]) -> list[CpuArchCost]:
    front: list[CpuArchCost] = []
    for ca in costs:
        if not ca.feasible:
            continue
        if any(dominates(cb, ca) for cb in costs if cb.feasible and cb is not ca):
            continue
        front.append(ca)
    front.sort(key=lambda c: c.pareto_key())
    return front
