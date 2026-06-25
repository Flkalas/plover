"""MB-102 breadboard grid model."""

from __future__ import annotations

from dataclasses import dataclass

PITCH_MM = 2.54
HOLES_PER_STRIP = 5
CENTER_GAP_HOLES = 1  # center gap between E-E columns


@dataclass
class Mb102Coord:
    block: int
    row: int
    col: int


@dataclass
class DipFootprint:
    n_pins: int
    anchor_row: int
    anchor_col: int
    notch: str = "up"


def px_to_mm(x_px: float, y_px: float, *, px_per_mm: float = 1.0 / 0.35) -> tuple[float, float]:
    return x_px / px_per_mm, y_px / px_per_mm


def snap_dip_mb102(
    n_pins: int,
    x_mm: float,
    y_mm: float,
    *,
    block: int = 0,
) -> Mb102Coord:
    """Snap DIP anchor (pin1) to breadboard hole grid."""
    col = max(0, int(round(x_mm / PITCH_MM)))
    row = max(0, int(round(y_mm / PITCH_MM)))
    return Mb102Coord(block=block, row=row, col=col)


def dip_occupies(n_pins: int) -> tuple[int, int]:
    """Rows × cols holes occupied (DIP spans center gap for 14/16)."""
    half = n_pins // 2
    return half, 2 if n_pins >= 14 else 1


def overlaps(a: DipFootprint, b: DipFootprint, block_a: int, block_b: int) -> bool:
    if block_a != block_b:
        return False
    ra, ca = dip_occupies(a.n_pins)
    rb, cb = dip_occupies(b.n_pins)
    return not (
        a.anchor_col + ca <= b.anchor_col
        or b.anchor_col + cb <= a.anchor_col
        or a.anchor_row + ra <= b.anchor_row
        or b.anchor_row + rb <= a.anchor_row
    )
