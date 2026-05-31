"""8-bit control word fields."""

from __future__ import annotations

from dataclasses import dataclass

CW_FLASH_BASE = 0x4000


@dataclass(frozen=True)
class ControlWord:
    raw: int

    @property
    def alu_op(self) -> int:
        return (self.raw >> 4) & 0xF

    @property
    def reg_we(self) -> bool:
        return bool((self.raw >> 3) & 1)

    @property
    def y_oe(self) -> bool:
        return bool((self.raw >> 2) & 1)

    @property
    def mem_rd(self) -> bool:
        return bool((self.raw >> 1) & 1)

    @property
    def mem_wr(self) -> bool:
        return bool(self.raw & 1)


def cs_index(opcode: int, phase: int) -> int:
    return ((opcode & 0xF) << 2) | (phase & 3)


def lookup_cw(nor_read_fn, opcode: int, phase: int) -> ControlWord:
    idx = cs_index(opcode, phase)
    return ControlWord(nor_read_fn(idx))
