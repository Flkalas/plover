"""Software return stack — calling-convention-v0.1 / software-memory-layout."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulators.cyclesim.blocks.fetch import MemArray

RP_CELL = 0x0F00
STACK_BASE = 0xF600
STACK_TOP = 0xFEEF


class StackError(Exception):
    """Return stack overflow or underflow."""


class ReturnStack:
    """RP @ $0F00 (16-bit LE); stack cells $F600–$FEEF grow upward."""

    def __init__(self, mem: MemArray) -> None:
        self.mem = mem

    def _read16(self, addr: int) -> int:
        return (self.mem.read(addr) & 0xFF) | ((self.mem.read(addr + 1) & 0xFF) << 8)

    def _write16(self, addr: int, val: int) -> None:
        val &= 0xFFFF
        self.mem.write(addr, val & 0xFF)
        self.mem.write(addr + 1, (val >> 8) & 0xFF)

    def read_rp(self) -> int:
        return self._read16(RP_CELL)

    def write_rp(self, rp: int) -> None:
        self._write16(RP_CELL, rp & 0xFFFF)

    def push_return(self, pc: int) -> None:
        rp = self.read_rp()
        if rp > STACK_TOP - 1:
            raise StackError("return stack overflow")
        self._write16(rp, pc & 0xFFFF)
        self.write_rp((rp + 2) & 0xFFFF)

    def pop_return(self) -> int:
        rp = self.read_rp()
        if rp <= STACK_BASE:
            raise StackError("return stack underflow")
        rp -= 2
        pc = self._read16(rp)
        self.write_rp(rp)
        return pc
