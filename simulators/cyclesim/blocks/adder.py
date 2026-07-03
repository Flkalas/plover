"""4-bit ripple adder (283 half) functional block."""

from __future__ import annotations


def add4(a: int, b: int, cin: int) -> tuple[int, int]:
    s = (a + b + cin) & 0xF
    cout = 1 if (a + b + cin) > 0xF else 0
    return s, cout


def add8(a: int, b: int, cin: int) -> tuple[int, int]:
    lo, c1 = add4(a & 0xF, b & 0xF, cin)
    hi, cout = add4((a >> 4) & 0xF, (b >> 4) & 0xF, c1)
    return lo | (hi << 4), cout
