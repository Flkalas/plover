"""Shared ALU opcode test vectors for hwsim tests and breadboard cheat sheet."""

from __future__ import annotations

# mux2 data (2C3..2C0) = bctrl3..0; sel = A|B<<1 on shared 153 A/B pins
BCTRL_ADD = (0, 0, 1, 1)  # C0=0 C2/C3=1 — B[i] pass
BCTRL_SUB = (1, 1, 0, 0)  # C0/C1=1 C2/C3=0 — ~B[i]
BCTRL_DEC = (1, 1, 1, 1)  # 1111 — constant 1
BCTRL_NOP = (0, 0, 0, 0)


def bits(prefix: str, val: int) -> dict[str, int]:
    return {f"{prefix}{i}": (val >> i) & 1 for i in range(8)}


def ctrl(
    *,
    cin: int = 0,
    s0: int = 0,
    s1: int = 0,
    bctrl: tuple[int, int, int, int] = BCTRL_NOP,
    inc_en: int = 0,
    lgc0: int = 0,
    lgc1: int = 0,
    lgc2: int = 0,
    lgc3: int = 0,
) -> dict[str, int]:
    """Control nets for pure Gigatron B_CTRL alu8."""
    return {
        "net_cin": cin,
        "net_153_s0": s0,
        "net_153_s1": s1,
        "net_bctrl0": bctrl[0],
        "net_bctrl1": bctrl[1],
        "net_bctrl2": bctrl[2],
        "net_bctrl3": bctrl[3],
        "net_inc_en": inc_en,
        "net_lgc0": lgc0,
        "net_lgc1": lgc1,
        "net_lgc2": lgc2,
        "net_lgc3": lgc3,
    }


# (name, A, B, expected_Y, control)
CASES: list[tuple[str, int, int, int, dict[str, int]]] = [
    ("NOP", 0x00, 0x00, 0x00, ctrl()),
    ("ADD", 0x12, 0x34, 0x46, ctrl(bctrl=BCTRL_ADD)),
    ("SUB", 0x12, 0x34, 0xDE, ctrl(cin=1, bctrl=BCTRL_SUB)),
    ("AND", 0x12, 0x34, 0x10, ctrl(s0=1, lgc3=1)),
    ("OR", 0x12, 0x34, 0x36, ctrl(s1=1, lgc1=1, lgc2=1, lgc3=1)),
    ("XOR", 0x12, 0x34, 0x26, ctrl(s0=1, s1=1, lgc1=1, lgc2=1)),
    ("NOT", 0x12, 0x00, 0xED, ctrl(s0=1, s1=1, lgc0=1)),
    ("PASS_A", 0x12, 0xFF, 0x12, ctrl(s0=1, lgc3=1)),
    ("PASS_B", 0xFF, 0x34, 0x34, ctrl(s0=1, lgc3=1)),
    ("INC", 0x12, 0x00, 0x13, ctrl(inc_en=1)),
    ("DEC", 0x12, 0x00, 0x11, ctrl(bctrl=BCTRL_DEC)),
    ("CMP", 0x12, 0x34, 0xDE, ctrl(cin=1, bctrl=BCTRL_SUB)),
]

OPCODE_NAMES = {i: name for i, (name, *_rest) in enumerate(CASES)}

LOGIC_C: dict[int, tuple[int, int, int, int]] = {
    0: (0, 0, 0, 0),
    3: (0, 0, 0, 1),
    4: (0, 1, 1, 1),
    5: (0, 1, 1, 0),
    6: (1, 0, 0, 0),
    7: (0, 0, 0, 1),
    8: (0, 0, 0, 1),
}
