"""ALU8 row-grid layout template: columns, corridors, port alignment."""

from __future__ import annotations

from dataclasses import dataclass

from simulators.cyclesim.export.schematic.types import PinAnchor

GRID = 10.0
MARGIN = 100.0
ROW_PITCH = 80.0
ROW_GAP = 20.0
IO_STRIP_W = GRID * 16
COL_GAP = 120.0
PITCH_X = 280.0
PIN_PITCH = GRID * 2
PIN_INSET = GRID * 2
PIN_LEN = GRID * 2
LANE = GRID * 2
BODY_W_153 = GRID * 10
BODY_H_153 = ROW_PITCH - ROW_GAP
BODY_W_WIDE = GRID * 12
A_ROW_OFFSET = PIN_INSET
B_ROW_OFFSET = PIN_INSET + PIN_PITCH
Y_ROW_OFFSET = PIN_INSET
B_PIN_COL_X = PIN_PITCH * 2

BUS_TOP = {f"net_lgc{i}" for i in range(4)}
BUS_BOTTOM = {f"net_bctrl{i}" for i in range(4)}
BUS_CTRL_LEFT = {"net_cin", "net_153_s0", "net_153_s1"}

ORPHAN_PORTS = frozenset({"net_153_s0", "net_153_s1", "net_cmp_z", "net_cmp_c_ge"})


def snap(v: float, grid: float = GRID) -> float:
    return round(v / grid) * grid


@dataclass(frozen=True)
class Alu8Template:
    left_io: float
    right_io: float
    col_153: float
    col_283: float
    col_157: float
    body_w_153: float
    body_h_153: float
    row_y: tuple[float, ...]
    lgc_rail_y: dict[str, float]
    bctrl_rail_y: dict[str, float]
    ctrl_rail_y: dict[str, float]
    y_mux_rail_y: float
    flag_rail_y: dict[str, float]
    ch_153_283: float
    ch_283_157: float
    port_x_a: float
    port_x_b: float
    port_x_ctrl: float
    port_x_right: float
    port_tap_x: float
    height: float


def build_alu8_template() -> Alu8Template:
    left_io = snap(MARGIN)
    port_x_a = snap(left_io + GRID * 2)
    port_x_b = snap(left_io + GRID * 6)
    port_x_ctrl = snap(left_io + GRID * 12)
    port_tap_x = snap(left_io + IO_STRIP_W - GRID * 2)

    top_base = snap(MARGIN + GRID * 2)
    ctrl_rail_y = {
        "net_cin": snap(top_base),
        "net_153_s0": snap(top_base + LANE),
        "net_153_s1": snap(top_base + LANE * 2),
    }
    lgc_base = snap(top_base + LANE * 4)
    lgc_rail_y = {f"net_lgc{i}": snap(lgc_base + i * LANE) for i in range(4)}

    row0 = snap(lgc_base + LANE * 5)
    row_y = tuple(snap(row0 + i * ROW_PITCH) for i in range(8))

    bctrl_base = snap(row_y[7] + BODY_H_153 + GRID * 2)
    bctrl_rail_y = {f"net_bctrl{i}": snap(bctrl_base + i * LANE) for i in range(4)}

    y_mux_rail_y = snap(bctrl_base + LANE * 5)
    flag_base = snap(row_y[7] + BODY_H_153 + GRID * 4)
    flag_rail_y = {
        "net_cmp_z": snap(flag_base),
        "net_cmp_c_ge": snap(flag_base + LANE),
        "net_c_hi": snap(flag_base + LANE * 2),
    }

    col_153 = snap(left_io + IO_STRIP_W)
    col_283 = snap(col_153 + BODY_W_153 + COL_GAP + PITCH_X - BODY_W_153)
    col_283 = snap(col_153 + PITCH_X + COL_GAP)
    col_157 = snap(col_283 + PITCH_X + COL_GAP)
    body_w_153 = BODY_W_153
    body_h_153 = BODY_H_153

    right_io = snap(col_157 + BODY_W_WIDE + IO_STRIP_W)
    port_x_right = snap(right_io - GRID * 2)

    ch_153_283 = snap(col_153 + body_w_153 + (col_283 - col_153 - body_w_153) / 2)
    ch_283_157 = snap(col_283 + BODY_W_WIDE + (col_157 - col_283 - BODY_W_WIDE) / 2)

    height = snap(y_mux_rail_y + MARGIN)

    return Alu8Template(
        left_io=left_io,
        right_io=right_io,
        col_153=col_153,
        col_283=col_283,
        col_157=col_157,
        body_w_153=body_w_153,
        body_h_153=body_h_153,
        row_y=row_y,
        lgc_rail_y=lgc_rail_y,
        bctrl_rail_y=bctrl_rail_y,
        ctrl_rail_y=ctrl_rail_y,
        y_mux_rail_y=y_mux_rail_y,
        flag_rail_y=flag_rail_y,
        ch_153_283=ch_153_283,
        ch_283_157=ch_283_157,
        port_x_a=port_x_a,
        port_x_b=port_x_b,
        port_x_ctrl=port_x_ctrl,
        port_x_right=port_x_right,
        port_tap_x=port_tap_x,
        height=height,
    )


def chip_positions(tmpl: Alu8Template) -> dict[str, tuple[float, float, float, float]]:
    """ref -> (ox, oy, body_w, body_h)."""
    pos: dict[str, tuple[float, float, float, float]] = {}
    for i in range(8):
        pos[f"U_ALU_153_{i}"] = (tmpl.col_153, tmpl.row_y[i], tmpl.body_w_153, tmpl.body_h_153)
    pos["U_ALU_283_LO"] = (tmpl.col_283, tmpl.row_y[0], BODY_W_WIDE, ROW_PITCH * 4 - ROW_GAP)
    pos["U_ALU_283_HI"] = (tmpl.col_283, tmpl.row_y[4], BODY_W_WIDE, ROW_PITCH * 4 - ROW_GAP)
    pos["U_ALU_157_YBP_0"] = (tmpl.col_157, tmpl.row_y[0], BODY_W_WIDE, ROW_PITCH * 4 - ROW_GAP)
    pos["U_ALU_157_YBP_1"] = (tmpl.col_157, tmpl.row_y[4], BODY_W_WIDE, ROW_PITCH * 4 - ROW_GAP)
    return pos


def port_label_positions(
    tmpl: Alu8Template,
    port_names: set[str],
) -> dict[str, tuple[float, float, str]]:
    labels: dict[str, tuple[float, float, str]] = {}

    for i in range(8):
        ay = snap(tmpl.row_y[i] + A_ROW_OFFSET)
        by = snap(tmpl.row_y[i] + B_ROW_OFFSET)
        if f"net_a{i}" in port_names:
            labels[f"net_a{i}"] = (tmpl.port_x_a, ay, "left")
        if f"net_b{i}" in port_names:
            labels[f"net_b{i}"] = (tmpl.port_x_b, by, "left")
        if f"net_y{i}" in port_names:
            labels[f"net_y{i}"] = (tmpl.port_x_right, snap(tmpl.row_y[i] + Y_ROW_OFFSET), "right")

    for net, y in tmpl.lgc_rail_y.items():
        if net in port_names:
            labels[net] = (tmpl.port_x_ctrl, y, "left")

    for net, y in tmpl.bctrl_rail_y.items():
        if net in port_names:
            labels[net] = (tmpl.port_x_ctrl, y, "left")

    for net, y in tmpl.ctrl_rail_y.items():
        if net in port_names:
            labels[net] = (tmpl.port_x_ctrl, y, "left")

    if "net_y_mux_sel" in port_names:
        labels["net_y_mux_sel"] = (tmpl.port_x_ctrl, tmpl.y_mux_rail_y, "left")

    for net, y in tmpl.flag_rail_y.items():
        if net in port_names:
            labels[net] = (tmpl.port_x_right, y, "right")

    return labels


def port_anchor_x(side: str, tmpl: Alu8Template) -> float:
    return tmpl.port_tap_x if side == "left" else tmpl.port_x_right


def chip_obstacles(instances: list[dict]) -> list[tuple[float, float, float, float]]:
    """Chip body rectangles with small margin."""
    margin = GRID
    return [
        (
            inst["x"] - margin,
            inst["y"] - margin,
            inst["w"] + margin * 2,
            inst["h"] + margin * 2,
        )
        for inst in instances
    ]


def stub_tip(anchor: PinAnchor) -> tuple[float, float]:
    if anchor.side == "left":
        return anchor.x - PIN_LEN, anchor.y
    if anchor.side == "right":
        return anchor.x + PIN_LEN, anchor.y
    if anchor.side == "top":
        return anchor.x, anchor.y - PIN_LEN
    return anchor.x, anchor.y + PIN_LEN
