"""Shared ALU opcode test vectors for hwsim tests and breadboard cheat sheet."""

from __future__ import annotations


def bits(prefix: str, val: int) -> dict[str, int]:
    return {f"{prefix}{i}": (val >> i) & 1 for i in range(8)}


def ctrl(
    sub: int = 0,
    cin: int = 0,
    s0: int = 0,
    s1: int = 0,
    b_sel: int = 0,
    b_const_sel: int = 0,
    b_const_hi: int = 0,
    lgc0: int = 0,
    lgc1: int = 0,
    lgc2: int = 0,
    lgc3: int = 0,
) -> dict[str, int]:
    """Control nets for alu8 Phase A (153_B: sel = b_sel | (b_const_sel<<1))."""
    # DEC: b_const_sel=1 and b_sel=1 (C3). INC: b_const_sel=1, b_sel=0 (C2).
    if b_const_sel and b_const_hi:
        b_sel = 1
    out = {
        "net_cin": cin,
        "net_153_s0": s0,
        "net_153_s1": s1,
        "net_b_sel": b_sel,
        "net_b_const_sel": b_const_sel,
    }
    for i in range(1, 8):
        out[f"net_b_const_bit{i}"] = b_const_hi
    out["net_lgc0"] = lgc0
    out["net_lgc1"] = lgc1
    out["net_lgc2"] = lgc2
    out["net_lgc3"] = lgc3
    return out


# (name, A, B, expected_Y, control)
CASES: list[tuple[str, int, int, int, dict[str, int]]] = [
    ("NOP", 0x00, 0x00, 0x00, ctrl()),
    ("ADD", 0x12, 0x34, 0x46, ctrl()),
    ("SUB", 0x12, 0x34, 0xDE, ctrl(cin=1, b_sel=1)),
    ("AND", 0x12, 0x34, 0x10, ctrl(s0=1, lgc3=1)),
    ("OR", 0x12, 0x34, 0x36, ctrl(s1=1, lgc1=1, lgc2=1, lgc3=1)),
    ("XOR", 0x12, 0x34, 0x26, ctrl(s0=1, s1=1, lgc1=1, lgc2=1)),
    ("NOT", 0x12, 0x00, 0xED, ctrl(s0=1, s1=1, lgc0=1)),
    ("PASS_A", 0x12, 0xFF, 0x12, ctrl(s0=1, lgc3=1)),
    ("PASS_B", 0xFF, 0x34, 0x34, ctrl(s0=1, lgc3=1)),
    ("INC", 0x12, 0x00, 0x13, ctrl(b_const_sel=1, b_const_hi=0)),
    ("DEC", 0x12, 0x00, 0x11, ctrl(b_const_sel=1, b_const_hi=1)),
    ("CMP", 0x12, 0x34, 0xDE, ctrl(cin=1, b_sel=1)),
]

OPCODE_NAMES = {i: name for i, (name, *_rest) in enumerate(CASES)}

# Gigatron 153 C0..C3 (shared across 8 bit-slices); see docs/hardware/alu8-phase-b.md
LOGIC_C: dict[int, tuple[int, int, int, int]] = {
    0: (0, 0, 0, 0),
    3: (0, 0, 0, 1),
    4: (0, 1, 1, 1),
    5: (0, 1, 1, 0),
    6: (1, 0, 0, 0),
    7: (0, 0, 0, 1),
    8: (0, 0, 0, 1),
}
