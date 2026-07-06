"""TFR ISA variant decoders — fit-study only (not v1.0 normative)."""

from __future__ import annotations

from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr, encode_tfr, is_tfr_valid

# --- TFR-v10 (baseline) ---


def decode_tfr_v10(opcode: int) -> tuple[int, int] | None:
    if not is_tfr_valid(opcode):
        return None
    return decode_tfr(opcode)


# --- TFR-3bit: 0x10 | idx[2:0] ---

TFR_3BIT_MAP: tuple[tuple[int, int], ...] = (
    (1, 0),  # idx0 TFR01 R0<-R1
    (2, 0),  # idx1 TFR02
    (0, 1),  # idx2 TFR10
    (2, 1),  # idx3 TFR12
    (0, 2),  # idx4 TFR20
    (1, 2),  # idx5 TFR21
)


def encode_tfr_3bit(src: int, dst: int) -> int:
    for idx, (s, d) in enumerate(TFR_3BIT_MAP):
        if s == src and d == dst:
            return 0x10 | idx
    raise ValueError(f"invalid TFR src={src} dst={dst}")


def decode_tfr_3bit(opcode: int) -> tuple[int, int] | None:
    op = opcode & 0x1F
    if (op & 0x18) != 0x10:
        return None
    idx = op & 0x7
    if idx > 5:
        return None
    src, dst = TFR_3BIT_MAP[idx]
    return src, dst


def is_tfr_valid_3bit(opcode: int) -> bool:
    return decode_tfr_3bit(opcode) is not None


# --- TFR-ring-2bit: hot 3 only ---

RING_2BIT_MAP: dict[int, tuple[int, int]] = {
    0b00: (1, 0),  # R0<-R1
    0b01: (2, 1),  # R1<-R2
    0b10: (0, 2),  # R2<-R0
}


def decode_tfr_ring_2bit(opcode: int) -> tuple[int, int] | None:
    op = opcode & 0x1F
    if (op & 0x1C) != 0x10:
        return None
    ring = op & 0x3
    return RING_2BIT_MAP.get(ring)


def ring_2bit_cold_expand(src: int, dst: int) -> list[tuple[int, int]]:
    """Return 2-insn ring sequence (src,dst) pairs with GPR clobber on middle reg."""
    # R0<-R2: R1<-R2 then R0<-R1 (clobber R1)
    cold: dict[tuple[int, int], list[tuple[int, int]]] = {
        (2, 0): [(2, 1), (1, 0)],
        (0, 1): [(0, 2), (2, 1)],
        (1, 2): [(1, 0), (0, 2)],
    }
    return cold[(src, dst)]


# --- TFR-ring-macro: ring + 2-hop in hardware (clobber) ---

def decode_tfr_ring_macro(opcode: int) -> tuple[int, int, int] | None:
    """Return (src, dst, hops) — hops=1 ring hot, hops=2 cold macro."""
    hot = decode_tfr_ring_2bit(opcode)
    if hot is not None:
        src, dst = hot
        return src, dst, 1
    op = opcode & 0x1F
    if (op & 0x10) != 0x10 or (op & 0x3) != 0x3:
        return None
    sub = (op >> 2) & 0x3
    cold_map = {0: (2, 0), 1: (0, 1), 2: (1, 2)}
    if sub not in cold_map:
        return None
    src, dst = cold_map[sub]
    return src, dst, 2


# --- TFR-tmp-2op: 4 reg, 2 micro-op, no clobber ---

TMP = 3

RING_TMP_MAP: dict[int, tuple[int, int]] = {
    0b00: (1, 0),
    0b01: (2, 1),
    0b10: (0, 2),
}

COLD_TMP_SUB: dict[int, tuple[int, int]] = {
    0b00: (2, 0),
    0b01: (0, 1),
    0b10: (1, 2),
}


def decode_tfr_tmp_2op(opcode: int) -> tuple[int, int] | None:
    op = opcode & 0x1F
    if (op & 0x10) != 0x10:
        return None
    low = op & 0x3
    if low != 0b11:
        return RING_TMP_MAP.get(low)
    sub = (op >> 2) & 0x3
    return COLD_TMP_SUB.get(sub)


def tfr_tmp_2op_micro_ops(src: int, dst: int) -> list[tuple[int, int, int]]:
    """Return [(write_sel, read_sel, data_src), ...] for ph0/ph1. write_sel may be TMP=3."""
    return [
        (TMP, src, src),  # TMP <- src
        (dst, TMP, TMP),  # dst <- TMP
    ]


# --- helpers ---

ALL_TFR_PAIRS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (2, 0),
    (0, 1),
    (2, 1),
    (0, 2),
    (1, 2),
)


def v10_opcode_for_pair(src: int, dst: int) -> int:
    return encode_tfr(src, dst)


def pairs_reachable_ring_2bit() -> set[tuple[int, int]]:
    return set(RING_2BIT_MAP.values())


def pairs_reachable_tmp_2op() -> set[tuple[int, int]]:
    out = set(RING_TMP_MAP.values()) | set(COLD_TMP_SUB.values())
    return out
