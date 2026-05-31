"""opcode × phase → Reg_Sel[1:0] PLA."""

from __future__ import annotations

REG_SEL_TABLE: dict[tuple[int, int], int] = {
    (0x01, 0): 0,
    (0x01, 1): 1,
    (0x01, 2): 2,
    (0x02, 0): 0,
    (0x02, 1): 0,
    (0x03, 0): 0,
    (0x03, 1): 0,
    (0x04, 0): 0,
    (0x04, 1): 0,
    (0x05, 0): 0,
    (0x06, 0): 0,
    (0x07, 0): 0,
    (0x08, 0): 0,
    (0x08, 1): 0,
    (0x09, 0): 0,
    (0x09, 1): 0,
    (0x0A, 0): 0,
}


def reg_sel(opcode: int, phase: int) -> int:
    return REG_SEL_TABLE.get((opcode & 0xF, phase & 3), 0)
