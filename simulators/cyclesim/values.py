"""Logic value encoding for structural cycle simulation."""

from __future__ import annotations

L = 0
H = 1
X = 2
Z = 3

VALUE_NAMES = {L: "L", H: "H", X: "X", Z: "Z"}


def bit(v: int, i: int) -> int:
    return (v >> i) & 1


def from_bits(bits: list[int]) -> int:
    out = 0
    for i, b in enumerate(bits):
        out |= (b & 1) << i
    return out


def to_bits(v: int, width: int = 8) -> list[int]:
    return [(v >> i) & 1 for i in range(width)]
