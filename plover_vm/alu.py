"""8-bit ALU — 12 alu_sel operations (combinational)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AluResult:
    y: int
    cout: bool
    zero: bool


def alu8(a: int, b: int, alu_sel: int) -> AluResult:
    a &= 0xFF
    b &= 0xFF
    sel = alu_sel & 0xF

    if sel == 0:  # NOP
        y = 0
        cout = False
    elif sel == 1:  # ADD
        s = a + b
        y = s & 0xFF
        cout = s > 0xFF
    elif sel == 2:  # SUB / CMP
        s = a + ((~b) & 0xFF) + 1
        y = s & 0xFF
        cout = s > 0xFF
    elif sel == 3:  # AND
        y = a & b
        cout = False
    elif sel == 4:  # OR
        y = a | b
        cout = False
    elif sel == 5:  # XOR
        y = a ^ b
        cout = False
    elif sel == 6:  # NOT
        y = (~a) & 0xFF
        cout = False
    elif sel == 7:  # PASS_A
        y = a & 0xFF
        cout = False
    elif sel == 8:  # PASS_B
        y = b & 0xFF
        cout = False
    elif sel == 9:  # INC
        s = a + 1
        y = s & 0xFF
        cout = s > 0xFF
    elif sel == 10:  # DEC
        s = a + 0xFF
        y = s & 0xFF
        cout = s > 0xFF
    elif sel == 11:  # CMP (same as SUB, discard y for flags)
        s = a + ((~b) & 0xFF) + 1
        y = s & 0xFF
        cout = s > 0xFF
    else:
        y = 0
        cout = False

    return AluResult(y=y, cout=cout, zero=(y & 0xFF) == 0)
