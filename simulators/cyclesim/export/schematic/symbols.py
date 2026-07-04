"""Chip symbol geometry with row-aligned pin placement for ALU8."""

from __future__ import annotations

from typing import Any

from simulators.cyclesim.export.schematic.alu8_template import (
    A_ROW_OFFSET,
    B_PIN_COL_X,
    B_ROW_OFFSET,
    BODY_W_153,
    BODY_W_WIDE,
    PIN_INSET,
    PIN_LEN,
    PIN_PITCH,
    Y_ROW_OFFSET,
    Alu8Template,
    chip_positions,
    snap,
)
from simulators.cyclesim.export.schematic.types import PinAnchor, PinSpec

PART_PINS: dict[str, list[PinSpec]] = {
    "74HC153": [
        PinSpec("A", "left", 0),
        PinSpec("B", "left", 1),
        PinSpec("1Y", "right", 0),
        PinSpec("2Y", "right", 1),
        PinSpec("1C0", "top", 0),
        PinSpec("1C1", "top", 1),
        PinSpec("1C2", "top", 2),
        PinSpec("1C3", "top", 3),
        PinSpec("2C0", "bottom", 0),
        PinSpec("2C1", "bottom", 1),
        PinSpec("2C2", "bottom", 2),
        PinSpec("2C3", "bottom", 3),
    ],
    "74HC283": [
        PinSpec("A0", "left", 0),
        PinSpec("A1", "left", 1),
        PinSpec("A2", "left", 2),
        PinSpec("A3", "left", 3),
        PinSpec("B0", "left", 4),
        PinSpec("B1", "left", 5),
        PinSpec("B2", "left", 6),
        PinSpec("B3", "left", 7),
        PinSpec("CIN", "left", 8),
        PinSpec("S0", "right", 0),
        PinSpec("S1", "right", 1),
        PinSpec("S2", "right", 2),
        PinSpec("S3", "right", 3),
        PinSpec("COUT", "right", 4),
    ],
    "74HC157": [
        PinSpec("1A", "left", 0),
        PinSpec("2A", "left", 1),
        PinSpec("3A", "left", 2),
        PinSpec("4A", "left", 3),
        PinSpec("1B", "left", 4),
        PinSpec("2B", "left", 5),
        PinSpec("3B", "left", 6),
        PinSpec("4B", "left", 7),
        PinSpec("S", "top", 1),
        PinSpec("1Y", "right", 0),
        PinSpec("2Y", "right", 1),
        PinSpec("3Y", "right", 2),
        PinSpec("4Y", "right", 3),
    ],
}


def _153_pin(
    ox: float,
    oy: float,
    body_w: float,
    body_h: float,
    spec: PinSpec,
) -> tuple[float, float, str]:
    if spec.side == "left":
        y = snap(oy + (A_ROW_OFFSET if spec.order == 0 else B_ROW_OFFSET))
        return snap(ox), y, "left"
    if spec.side == "right":
        y = snap(oy + (A_ROW_OFFSET if spec.order == 0 else B_ROW_OFFSET))
        return snap(ox + body_w), y, "right"
    if spec.side == "top":
        x = snap(ox + PIN_INSET + spec.order * PIN_PITCH)
        return x, snap(oy), "top"
    x = snap(ox + PIN_INSET + spec.order * PIN_PITCH)
    return x, snap(oy + body_h), "bottom"


def _283_pin(
    ox: float,
    oy: float,
    body_w: float,
    body_h: float,
    spec: PinSpec,
    row_base: int,
    tmpl: Alu8Template,
) -> tuple[float, float, str]:
    if spec.name.startswith("A") and len(spec.name) == 2:
        bit = int(spec.name[1])
        y = snap(tmpl.row_y[row_base + bit] + A_ROW_OFFSET)
        return snap(ox), y, "left"
    if spec.name.startswith("B") and len(spec.name) == 2:
        bit = int(spec.name[1])
        y = snap(tmpl.row_y[row_base + bit] + B_ROW_OFFSET)
        return snap(ox), y, "left"
    if spec.name == "CIN":
        return snap(ox), snap(oy + body_h - PIN_INSET), "left"
    if spec.name.startswith("S") and len(spec.name) == 2:
        bit = int(spec.name[1])
        y = snap(tmpl.row_y[row_base + bit] + A_ROW_OFFSET)
        return snap(ox + body_w), y, "right"
    if spec.name == "COUT":
        y = snap(tmpl.row_y[row_base + 3] + B_ROW_OFFSET)
        return snap(ox + body_w), y, "right"
    return snap(ox), snap(oy), "left"


def _157_pin(
    ox: float,
    oy: float,
    body_w: float,
    body_h: float,
    spec: PinSpec,
    row_base: int,
    tmpl: Alu8Template,
) -> tuple[float, float, str]:
    if spec.name == "S":
        x = snap(ox + body_w / 2)
        return x, snap(oy), "top"
    if spec.name.endswith("A"):
        bit = int(spec.name[0]) - 1
        y = snap(tmpl.row_y[row_base + bit] + A_ROW_OFFSET)
        return snap(ox), y, "left"
    if spec.name.endswith("B"):
        bit = int(spec.name[0]) - 1
        y = snap(tmpl.row_y[row_base + bit] + B_ROW_OFFSET)
        return snap(ox), y, "left"
    if spec.name.endswith("Y"):
        bit = int(spec.name[0]) - 1
        y = snap(tmpl.row_y[row_base + bit] + Y_ROW_OFFSET)
        return snap(ox + body_w), y, "right"
    return snap(ox), snap(oy), "left"


def pin_position(
    ref: str,
    part: str,
    spec: PinSpec,
    ox: float,
    oy: float,
    body_w: float,
    body_h: float,
    tmpl: Alu8Template,
) -> tuple[float, float, str]:
    if part == "74HC153":
        return _153_pin(ox, oy, body_w, body_h, spec)
    if part == "74HC283":
        row_base = 0 if ref == "U_ALU_283_LO" else 4
        return _283_pin(ox, oy, body_w, body_h, spec, row_base, tmpl)
    if part == "74HC157":
        row_base = 0 if ref == "U_ALU_157_YBP_0" else 4
        return _157_pin(ox, oy, body_w, body_h, spec, row_base, tmpl)
    raise ValueError(f"unknown part {part}")


def place_instances(
    netlist: dict[str, Any],
    tmpl: Alu8Template,
) -> tuple[list[dict[str, Any]], list[PinAnchor]]:
    positions = chip_positions(tmpl)
    placed: list[dict[str, Any]] = []
    anchors: list[PinAnchor] = []

    for inst in netlist["instances"]:
        ref = inst["ref"]
        part = inst["part"]
        ox, oy, body_w, body_h = positions[ref]
        placed.append(
            {
                "ref": ref,
                "part": part,
                "x": ox,
                "y": oy,
                "w": body_w,
                "h": body_h,
                "pins": inst["pins"],
            }
        )
        for spec in PART_PINS[part]:
            net = inst["pins"].get(spec.name)
            if not net:
                continue
            px, py, side = pin_position(ref, part, spec, ox, oy, body_w, body_h, tmpl)
            anchors.append(PinAnchor(ref=ref, pin=spec.name, net=net, x=px, y=py, side=side))

    return placed, anchors
