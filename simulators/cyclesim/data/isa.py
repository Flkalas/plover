"""ISA helpers — implements plover-whitepaper §6 / microcode-spec.md."""


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

# TFR: opc[4]=1, opc[3:2]=dst, opc[1:0]=src (src != dst, neither field is 11₂)
TFR_OPS = frozenset({0x11, 0x12, 0x14, 0x16, 0x18, 0x19})
WIDE_ABS16_OPS = frozenset({OP_BEQ, OP_JMP, OP_STA16})


def encode_tfr(src: int, dst: int) -> int:
    """Build TFR opcode from register indices (0=R0, 1=R1, 2=R2)."""
    if src == dst or src > 2 or dst > 2:
        raise ValueError(f"invalid TFR src={src} dst={dst}")
    return 0x10 | (dst << 2) | src


def decode_tfr(opcode: int) -> tuple[int, int]:
    """Return (src, dst) from bit-field TFR opcode."""
    op = opcode & 0x1F
    src = op & 0x3
    dst = (op >> 2) & 0x3
    return src, dst


def is_tfr_valid(opcode: int) -> bool:
    op = opcode & 0x1F
    if op not in TFR_OPS:
        return False
    src, dst = decode_tfr(op)
    return src < 3 and dst < 3 and src != dst


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
    op = opcode & 0xFF
    if is_tfr_valid(op):
        return 1
    return PHASE_COUNT.get(op, 1)


def insn_length(opcode: int) -> int:
    op = opcode & 0xFF
    if op in WIDE_ABS16_OPS:
        return 3
    if is_tfr_valid(op) or op == OP_HALT:
        return 1
    return 2
