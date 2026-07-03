"""Part → cycle model factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cyclesim.models.base import CycleModel

if TYPE_CHECKING:
    from cyclesim.engine import CycleContext
from cyclesim.models.comb import (
    AluInc2c2,
    AluIncBSel,
    AluCmpFromSub,
    AluYMuxSel,
    Hc04,
    Hc08,
    Hc153,
    Hc153Slice,
    Hc157,
    Hc283,
    Hc32,
    Hc86,
    YBusBuf,
)
from cyclesim.models.cpld import (
    CpldGprCtrl,
    CpldSystemCtrl,
    CpldSystemCtrlTier2,
    MemDecodeBreadboard,
)
from cyclesim.models.seq import CpldRegfile, Regfile574Gpr

_COMB: dict[str, type[CycleModel]] = {
    "CPLD_SYSTEM_CTRL": CpldSystemCtrl,
    "MEM_DECODE_BREADBOARD": MemDecodeBreadboard,
    "CPLD_GPR_CTRL": CpldGprCtrl,
    "CPLD_SYSTEM_CTRL_TIER2": CpldSystemCtrlTier2,
    "ATF1504AS": CpldGprCtrl,
    "74HC04": Hc04,
    "74HC08": Hc08,
    "74HC32": Hc32,
    "74HC86": Hc86,
    "74HC153": Hc153,
    "ALU_153_SLICE": Hc153Slice,
    "74HC157": Hc157,
    "74HC283": Hc283,
    "ALU_INC_B_SEL": AluIncBSel,
    "ALU_INC_2C2": AluInc2c2,
    "ALU_Y_MUX_SEL": AluYMuxSel,
    "ALU_CMP_SUB": AluCmpFromSub,
    "Y_BUS_BUF": YBusBuf,
}

_SEQ: dict[str, type[CycleModel]] = {
    "REGFILE_574_GPR": Regfile574Gpr,
    "CPLD_REGFILE": CpldRegfile,
}


def create_model(ref: str, part: str, pins: dict[str, str], ctx: "CycleContext") -> CycleModel:
    cls = _COMB.get(part) or _SEQ.get(part)
    if cls is None:
        raise ValueError(f"cyclesim: no model for part {part} ({ref})")
    return cls(ref, pins, ctx)


def is_sequential_part(part: str) -> bool:
    return part in _SEQ
