"""ISA helpers — microcode-spec.md."""

from __future__ import annotations

OP_ADD = 0x01
OP_LDA = 0x02
OP_STA = 0x03
OP_BEQ = 0x04
OP_JMP = 0x05
OP_HALT = 0x0A
OP_CMP = 0x0D
OP_LDIO = 0x08
OP_STIO = 0x09
OP_STA16 = 0x0F

TFR_OPS = frozenset(range(0x10, 0x16))
WIDE_ABS16_OPS = frozenset({OP_BEQ, OP_JMP, OP_STA16})

# XFER opcode -> (src, dst) microcode-spec.md §5
TFR_REG_MAP: dict[int, tuple[int, int]] = {
    0x10: (1, 0),
    0x11: (2, 0),
    0x12: (0, 1),
    0x13: (2, 1),
    0x14: (0, 2),
    0x15: (1, 2),
}

PHASE_COUNT: dict[int, int] = {
    OP_ADD: 3,
    OP_LDA: 2,
    OP_STA: 2,
    OP_BEQ: 2,
    OP_JMP: 1,
    OP_HALT: 1,
    OP_CMP: 3,
    OP_LDIO: 2,
    OP_STIO: 2,
    OP_STA16: 2,
    **{op: 1 for op in TFR_OPS},
}


def phase_count(opcode: int) -> int:
    return PHASE_COUNT.get(opcode & 0xFF, 1)


def insn_length(opcode: int) -> int:
    op = opcode & 0xFF
    if op in WIDE_ABS16_OPS:
        return 3
    if op in TFR_OPS or op == OP_HALT:
        return 1
    return 2
