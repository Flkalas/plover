"""4:1 and 2:1 multiplexers (153 / 157 functional blocks)."""

from __future__ import annotations

from simulators.cyclesim.values import X


def mux4(sel: int, c0: int, c1: int, c2: int, c3: int) -> int:
    if sel == X or any(v == X for v in (c0, c1, c2, c3)):
        return X
    return (c0, c1, c2, c3)[sel & 3]


def mux2(sel: int, a: int, b: int) -> int:
    if sel == X or a == X or b == X:
        return X
    return a if (sel & 1) == 0 else b


def mux4_byte(sel_per_bit: list[int], c0: int, c1: int, c2: int, c3: int) -> int:
    out = 0
    for i in range(8):
        bit = mux4(sel_per_bit[i], (c0 >> i) & 1, (c1 >> i) & 1, (c2 >> i) & 1, (c3 >> i) & 1)
        if bit == X:
            return X
        out |= bit << i
    return out
