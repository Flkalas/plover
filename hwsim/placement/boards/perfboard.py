"""Perfboard (universal PCB) grid model ??2.54 mm pitch, no center gap."""

from __future__ import annotations

from dataclasses import dataclass

from hwsim.placement.boards.mb102 import PITCH_MM, px_to_mm


@dataclass
class PerfCoord:
    row: int
    col: int


def snap_dip_perfboard(n_pins: int, x_mm: float, y_mm: float) -> PerfCoord:
    col = max(0, int(round(x_mm / PITCH_MM)))
    row = max(0, int(round(y_mm / PITCH_MM)))
    return PerfCoord(row=row, col=col)


def dip_occupies_perf(n_pins: int) -> tuple[int, int]:
    half = n_pins // 2
    # perfboard: both columns on same side row span, 0.3" = 3 holes apart
    return half, 3
