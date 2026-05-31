"""16-bit ALU helpers for plover_vm wide register path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Alu16Result:
    y: int
    cout: bool
    zero: bool


def add16(a: int, b: int) -> Alu16Result:
    a &= 0xFFFF
    b &= 0xFFFF
    s = a + b
    y = s & 0xFFFF
    return Alu16Result(y=y, cout=s > 0xFFFF, zero=y == 0)


def sub16(a: int, b: int) -> Alu16Result:
    """Unsigned subtract; cout=1 when a >= b."""
    a &= 0xFFFF
    b &= 0xFFFF
    s = a - b
    y = s & 0xFFFF
    return Alu16Result(y=y, cout=a >= b, zero=y == 0)


def cmp16_u(a: int, b: int) -> Alu16Result:
    """Compare unsigned: carry set if a >= b."""
    return sub16(a, b)
