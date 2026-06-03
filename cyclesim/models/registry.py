"""Part → cycle model factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cyclesim.models.base import CycleModel

if TYPE_CHECKING:
    from cyclesim.engine import CycleContext
from cyclesim.models.comb import (
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
from cyclesim.models.cpld import CpldSystemCtrl
from cyclesim.models.seq import Regfile574Gpr

_COMB: dict[str, type[CycleModel]] = {
    "CPLD_SYSTEM_CTRL": CpldSystemCtrl,
    "ATF1504AS": CpldSystemCtrl,
    "74HC04": Hc04,
    "74HC08": Hc08,
    "74HC32": Hc32,
    "74HC86": Hc86,
    "74HC153": Hc153,
    "ALU_153_SLICE": Hc153Slice,
    "74HC157": Hc157,
    "74HC283": Hc283,
    "ALU_Y_MUX_SEL": AluYMuxSel,
    "ALU_CMP_SUB": AluCmpFromSub,
    "Y_BUS_BUF": YBusBuf,
}

_SEQ: dict[str, type[CycleModel]] = {
    "REGFILE_574_GPR": Regfile574Gpr,
}


def create_model(ref: str, part: str, pins: dict[str, str], ctx: "CycleContext") -> CycleModel:
    cls = _COMB.get(part) or _SEQ.get(part)
    if cls is None:
        raise ValueError(f"cyclesim: no model for part {part} ({ref})")
    return cls(ref, pins, ctx)


def is_sequential_part(part: str) -> bool:
    return part in _SEQ
