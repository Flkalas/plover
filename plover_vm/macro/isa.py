"""v0.1 macro ISA opcodes."""

from __future__ import annotations

OP_ADD = 0x01
OP_LDA = 0x02
OP_STA = 0x03
OP_BEQ = 0x04
OP_JMP = 0x05
OP_CALL = 0x06
OP_RET = 0x07
OP_LDIO = 0x08
OP_STIO = 0x09
OP_HALT = 0x0A
OP_ADD_RR = 0x0B  # R2 <- R0 + R1
OP_MOV = 0x0C  # deprecated on breadboard; VM compat — use TFR opcodes
OP_CMP = 0x0D  # R0 - imm, set flags
OP_BCS = 0x0E  # branch if carry (unsigned >=)
OP_STA16 = 0x0F  # store R0 to abs16 (3-byte insn)

# Implied register transfer (v1.0 breadboard — 1 byte, no operand)
OP_TFR01 = 0x10  # R0 <- R1
OP_TFR02 = 0x11  # R0 <- R2
OP_TFR10 = 0x12  # R1 <- R0
OP_TFR12 = 0x13  # R1 <- R2
OP_TFR20 = 0x14  # R2 <- R0
OP_TFR21 = 0x15  # R2 <- R1

TFR_OPS = frozenset({OP_TFR01, OP_TFR02, OP_TFR10, OP_TFR12, OP_TFR20, OP_TFR21})

# VM-only 16-bit wide register ops (not on breadboard ISA)
OP_WADD_RR = 0x20  # W2 <- W0 + W1
OP_WMOV = 0x21  # imm: (dst<<4)|src
OP_WCMP16 = 0x22  # W0 vs imm16 unsigned

WIDE_IMM16_OPS = frozenset({OP_WCMP16})

# dst, src for TFR opcodes (R0=0, R1=1, R2=2)
TFR_REG_MAP: dict[int, tuple[int, int]] = {
    OP_TFR01: (0, 1),
    OP_TFR02: (0, 2),
    OP_TFR10: (1, 0),
    OP_TFR12: (1, 2),
    OP_TFR20: (2, 0),
    OP_TFR21: (2, 1),
}

PHASE_COUNTS: dict[int, int] = {
    OP_ADD: 3,
    OP_LDA: 2,
    OP_STA: 2,
    OP_BEQ: 2,
    OP_JMP: 1,
    OP_CALL: 1,
    OP_RET: 1,
    OP_LDIO: 2,
    OP_STIO: 2,
    OP_HALT: 1,
    OP_MOV: 1,
    OP_CMP: 3,
    OP_STA16: 2,
    OP_TFR01: 1,
    OP_TFR02: 1,
    OP_TFR10: 1,
    OP_TFR12: 1,
    OP_TFR20: 1,
    OP_TFR21: 1,
}

WIDE_ABS16_OPS = frozenset({OP_BEQ, OP_JMP, OP_CALL, OP_STA16})


def phase_count(opcode: int) -> int:
    return PHASE_COUNTS.get(opcode & 0xFF, 1)
