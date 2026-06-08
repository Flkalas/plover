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
OP_MOV = 0x0C  # imm: (dst<<4)|src
OP_CMP = 0x0D  # R0 - imm, set flags
OP_BCS = 0x0E  # branch if carry (unsigned >=)
OP_STA16 = 0x0F  # store R0 to abs16 (3-byte insn)

# 16-bit wide register ops (fast-path); WCMP16 is 3 bytes: op, imm_lo, imm_hi
OP_WADD_RR = 0x10  # W2 <- W0 + W1
OP_WMOV = 0x11  # imm: (dst<<4)|src
OP_WCMP16 = 0x12  # W0 vs imm16 unsigned

WIDE_IMM16_OPS = frozenset({OP_WCMP16})

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
}

WIDE_ABS16_OPS = frozenset({OP_BEQ, OP_JMP, OP_CALL, OP_STA16})


def phase_count(opcode: int) -> int:
    return PHASE_COUNTS.get(opcode & 0xFF, 1)
