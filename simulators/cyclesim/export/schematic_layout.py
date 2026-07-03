"""KiCad-style schematic layout and SVG export for cyclesim functional blocks."""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from typing import Any

PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"
ROUTE_STUB = 14.0
PIN_PITCH = 13.0
PIN_LEN = 16.0
BODY_W_DEFAULT = 88.0
MARGIN = 48.0
PITCH_X = 168.0
PITCH_Y = 92.0

_CONTROL_NET = re.compile(
    r"net_(cin|153_s[01]|bctrl[0-3]|lgc[0-3]|y_mux_sel)$",
)


@dataclass(frozen=True)
class PinSpec:
    name: str
    side: str  # left, right, top, bottom
    order: float


@dataclass
class PinAnchor:
    ref: str
    pin: str
    net: str
    x: float
    y: float
    side: str


@dataclass
class SchematicLayout:
    width: float
    height: float
    anchors: list[PinAnchor]
    instances: list[dict[str, Any]]


PART_PINS: dict[str, list[PinSpec]] = {
    "FB_MUX4_SLICE": [
        PinSpec("A", "left", 0),
        PinSpec("B", "left", 1),
        PinSpec("Y_LOGIC", "right", 0),
        PinSpec("Y_BADD", "right", 1),
        PinSpec("C0", "top", 0),
        PinSpec("C1", "top", 1),
        PinSpec("C2", "top", 2),
        PinSpec("C3", "top", 3),
        PinSpec("D0", "bottom", 0),
        PinSpec("D1", "bottom", 1),
        PinSpec("D2", "bottom", 2),
        PinSpec("D3", "bottom", 3),
    ],
    "FB_ADD4": [
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
    "FB_MUX2_Y": [
        PinSpec("A", "left", 0),
        PinSpec("B", "left", 1),
        PinSpec("S", "left", 2),
        PinSpec("Y", "right", 0),
    ],
    "ALU_Y_MUX_SEL": [
        PinSpec("S0", "left", 0),
        PinSpec("S1", "left", 1),
        PinSpec("SEL", "right", 0),
    ],
    "ALU_CMP_SUB": [
        PinSpec("Y0", "left", 0),
        PinSpec("Y1", "left", 1),
        PinSpec("Y2", "left", 2),
        PinSpec("Y3", "left", 3),
        PinSpec("Y4", "left", 4),
        PinSpec("Y5", "left", 5),
        PinSpec("Y6", "left", 6),
        PinSpec("Y7", "left", 7),
        PinSpec("C_HI", "left", 8),
        PinSpec("CIN", "left", 9),
        PinSpec("BCTRL0", "bottom", 0),
        PinSpec("BCTRL1", "bottom", 1),
        PinSpec("BCTRL2", "bottom", 2),
        PinSpec("BCTRL3", "bottom", 3),
        PinSpec("Z", "right", 0),
        PinSpec("C_GE", "right", 1),
    ],
}


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _is_control_net(net: str) -> bool:
    return bool(_CONTROL_NET.match(net))


def _net_color(net: str) -> str:
    h = hashlib.md5(net.encode()).hexdigest()[:6]
    r = 80 + (int(h[0:2], 16) * 175) // 255
    g = 100 + (int(h[2:4], 16) * 155) // 255
    b = 120 + (int(h[4:6], 16) * 135) // 255
    return f"#{r:02x}{g:02x}{b:02x}"


def _symbol_body_size(part: str) -> tuple[float, float]:
    specs = PART_PINS[part]
    left = max((s.order for s in specs if s.side == "left"), default=0) + 1
    right = max((s.order for s in specs if s.side == "right"), default=0) + 1
    top = max((s.order for s in specs if s.side == "top"), default=0) + 1
    bottom = max((s.order for s in specs if s.side == "bottom"), default=0) + 1
    vert = max(left, right, 2)
    horiz = max(top, bottom, 2)
    w = max(BODY_W_DEFAULT, horiz * PIN_PITCH + 24)
    h = max(48.0, vert * PIN_PITCH + 28)
    return w, h


def _pin_position(
    ox: float,
    oy: float,
    body_w: float,
    body_h: float,
    spec: PinSpec,
) -> tuple[float, float, str]:
    if spec.side == "left":
        y = oy + 18 + spec.order * PIN_PITCH
        return ox, y, "left"
    if spec.side == "right":
        y = oy + 18 + spec.order * PIN_PITCH
        return ox + body_w, y, "right"
    if spec.side == "top":
        x = ox + 18 + spec.order * PIN_PITCH
        return x, oy, "top"
    x = ox + 18 + spec.order * PIN_PITCH
    return x, oy + body_h, "bottom"


def _route_polyline(x1: float, y1: float, x2: float, y2: float, side: str) -> str:
    stub = ROUTE_STUB
    if side == "left":
        ex = x1 - stub
    elif side == "right":
        ex = x1 + stub
    elif side == "top":
        ey = y1 - stub
        return f"{x1:.1f},{y1:.1f} {x1:.1f},{ey:.1f} {x2:.1f},{y2:.1f}"
    else:
        ey = y1 + stub
        return f"{x1:.1f},{y1:.1f} {x1:.1f},{ey:.1f} {x2:.1f},{y2:.1f}"
    return f"{x1:.1f},{y1:.1f} {ex:.1f},{y1:.1f} {ex:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"


def _bit_y(bit: int) -> float:
    return MARGIN + 36 + bit * PITCH_Y


def _layout_alu8_positions() -> dict[str, tuple[float, float]]:
    col_mux4 = MARGIN + 100
    col_add = col_mux4 + PITCH_X + 40
    col_mux2 = col_add + PITCH_X + 40
    col_glue = col_mux2 + PITCH_X + 20

    pos: dict[str, tuple[float, float]] = {}
    for i in range(8):
        pos[f"U_MUX4_{i}"] = (col_mux4, _bit_y(i))
        pos[f"U_MUX2_Y_{i}"] = (col_mux2, _bit_y(i))
    pos["U_ADD_LO"] = (col_add, _bit_y(1))
    pos["U_ADD_HI"] = (col_add, _bit_y(5))
    pos["U_Y_MUX_SEL"] = (col_glue, _bit_y(0))
    pos["U_CMP_SUB"] = (col_glue, _bit_y(3))
    return pos


def _port_label_positions(port_names: set[str]) -> dict[str, tuple[float, float, str]]:
    """Global label positions: (x, y, side)."""
    labels: dict[str, tuple[float, float, str]] = {}
    left_x = MARGIN - 8
    right_x = MARGIN + 100 + PITCH_X * 3 + 120

    for i in range(8):
        if f"net_a{i}" in port_names:
            labels[f"net_a{i}"] = (left_x, _bit_y(i) + 18, "left")
        if f"net_b{i}" in port_names:
            labels[f"net_b{i}"] = (left_x - 52, _bit_y(i) + 34, "left")
        if f"net_y{i}" in port_names:
            labels[f"net_y{i}"] = (right_x + 80, _bit_y(i) + 18, "right")

    ctrl_left = [
        ("net_cin", _bit_y(0) - 20),
        ("net_153_s0", _bit_y(0) - 34),
        ("net_153_s1", _bit_y(0) - 48),
    ]
    for net, y in ctrl_left:
        if net in port_names:
            labels[net] = (left_x, y, "left")

    for i in range(4):
        if f"net_bctrl{i}" in port_names:
            labels[f"net_bctrl{i}"] = (left_x - 26, MARGIN + 8 + i * 14, "left")
        if f"net_lgc{i}" in port_names:
            labels[f"net_lgc{i}"] = (left_x - 26, MARGIN + 64 + i * 14, "left")

    if "net_y_mux_sel" in port_names:
        labels["net_y_mux_sel"] = (left_x, _bit_y(7) + 52, "left")

    right_flags = [
        ("net_cmp_z", _bit_y(7) + 20),
        ("net_cmp_c_ge", _bit_y(7) + 36),
        ("net_c_hi", _bit_y(7) + 52),
    ]
    for net, y in right_flags:
        if net in port_names:
            labels[net] = (right_x + 80, y, "right")

    return labels


def layout_alu8_schematic(
    netlist: dict[str, Any],
    *,
    port_names: set[str] | None = None,
) -> SchematicLayout:
    positions = _layout_alu8_positions()
    anchors: list[PinAnchor] = []
    placed: list[dict[str, Any]] = []
    max_x = 0.0
    max_y = 0.0

    for inst in netlist["instances"]:
        ref = inst["ref"]
        part = inst["part"]
        ox, oy = positions[ref]
        body_w, body_h = _symbol_body_size(part)
        max_x = max(max_x, ox + body_w + 120)
        max_y = max(max_y, oy + body_h + 40)
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
        specs = PART_PINS[part]
        for spec in specs:
            net = inst["pins"].get(spec.name)
            if not net:
                continue
            px, py, side = _pin_position(ox, oy, body_w, body_h, spec)
            anchors.append(PinAnchor(ref=ref, pin=spec.name, net=net, x=px, y=py, side=side))

    ports = port_names or set()
    port_labels = _port_label_positions(ports)
    for net, (lx, ly, side) in port_labels.items():
        ax = lx + (36 if side == "left" else -36)
        anchors.append(PinAnchor(ref="__port__", pin="", net=net, x=ax, y=ly, side=side))

    width = max_x + MARGIN
    height = max(max_y + MARGIN, _bit_y(7) + 120)
    return SchematicLayout(width=width, height=height, anchors=anchors, instances=placed)


def _render_global_label(net: str, x: float, y: float, side: str) -> str:
    color = "#d29922" if _is_control_net(net) else _net_color(net)
    if side == "left":
        pts = f"{x:.1f},{y:.1f} {x + 28:.1f},{y:.1f} {x + 28:.1f},{y - 10:.1f} {x + 36:.1f},{y:.1f} {x + 28:.1f},{y + 10:.1f} {x + 28:.1f},{y:.1f}"
        tx, anchor = x - 4, "end"
    else:
        pts = f"{x:.1f},{y:.1f} {x - 28:.1f},{y:.1f} {x - 28:.1f},{y - 10:.1f} {x - 36:.1f},{y:.1f} {x - 28:.1f},{y + 10:.1f} {x - 28:.1f},{y:.1f}"
        tx, anchor = x + 4, "start"
    return (
        f'<g class="global-label" data-net="{_esc(net)}">'
        f'<polyline class="lbl-flag" points="{pts}" fill="{color}" opacity="0.35" stroke="{color}" stroke-width="1"/>'
        f'<text class="net-label lbl-global" data-net="{_esc(net)}" x="{tx:.1f}" y="{y + 4:.1f}" '
        f'text-anchor="{anchor}" fill="{color}">{_esc(net)}</text>'
        f"</g>"
    )


def _render_symbol(inst: dict[str, Any]) -> str:
    ref = inst["ref"]
    part = inst["part"]
    ox, oy = inst["x"], inst["y"]
    body_w, body_h = inst["w"], inst["h"]
    specs = PART_PINS[part]
    lines = [
        f'<g class="symbol" data-ref="{_esc(ref)}">',
        f'<rect class="sym-body" x="{ox:.1f}" y="{oy:.1f}" width="{body_w:.1f}" height="{body_h:.1f}" '
        f'rx="2" fill="#161b22" stroke="#58a6ff" stroke-width="1.4"/>',
        f'<text class="lbl-ref" x="{ox + body_w / 2:.1f}" y="{oy + 12:.1f}" '
        f'text-anchor="middle">{_esc(ref)}</text>',
        f'<text class="lbl-part" x="{ox + body_w / 2:.1f}" y="{oy + body_h - 6:.1f}" '
        f'text-anchor="middle">{_esc(part)}</text>',
    ]
    for spec in specs:
        px, py, side = _pin_position(ox, oy, body_w, body_h, spec)
        if side == "left":
            x2 = px - PIN_LEN
            lx, anchor = px - PIN_LEN - 3, "end"
        elif side == "right":
            x2 = px + PIN_LEN
            lx, anchor = px + PIN_LEN + 3, "start"
        elif side == "top":
            y2 = py - PIN_LEN
            lx, ly, anchor = px, py - PIN_LEN - 3, "middle"
            lines.append(
                f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{y2:.1f}" '
                f'stroke="#8b949e" stroke-width="1"/>'
            )
            lines.append(
                f'<text class="lbl-pin" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{_esc(spec.name)}</text>'
            )
            continue
        else:
            y2 = py + PIN_LEN
            lx, ly, anchor = px, py + PIN_LEN + 10, "middle"
            lines.append(
                f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{y2:.1f}" '
                f'stroke="#8b949e" stroke-width="1"/>'
            )
            lines.append(
                f'<text class="lbl-pin" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{_esc(spec.name)}</text>'
            )
            continue
        lines.append(
            f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{x2:.1f}" y2="{py:.1f}" '
            f'stroke="#8b949e" stroke-width="1"/>'
        )
        lines.append(
            f'<text class="lbl-pin" x="{lx:.1f}" y="{py + 4:.1f}" text-anchor="{anchor}">{_esc(spec.name)}</text>'
        )
    lines.append("</g>")
    return "\n".join(lines)


def _render_wires(anchors: list[PinAnchor], port_labels: dict[str, tuple[float, float, str]]) -> str:
    by_net: dict[str, list[PinAnchor]] = {}
    for a in anchors:
        by_net.setdefault(a.net, []).append(a)

    elems: list[str] = []
    for net, pts in sorted(by_net.items()):
        if net in (PWR_VCC, PWR_GND):
            continue
        color = "#d29922" if _is_control_net(net) else _net_color(net)
        if len(pts) == 1:
            p = pts[0]
            elems.append(
                f'<g class="net orphan" data-net="{_esc(net)}">'
                f'<circle class="net-hub" data-net="{_esc(net)}" cx="{p.x:.1f}" cy="{p.y:.1f}" r="3" fill="{color}"/>'
                f'<text class="net-label lbl-net" data-net="{_esc(net)}" x="{p.x:.1f}" y="{p.y - 6:.1f}" '
                f'text-anchor="middle">{_esc(net)}</text></g>'
            )
            continue
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        elems.append(f'<g class="net" data-net="{_esc(net)}">')
        elems.append(
            f'<circle class="net-hub" data-net="{_esc(net)}" cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="{color}" opacity="0.9"/>'
        )
        for p in pts:
            poly = _route_polyline(p.x, p.y, cx, cy, p.side)
            elems.append(
                f'<polyline class="wire-hit" data-net="{_esc(net)}" data-ref="{_esc(p.ref)}" '
                f'points="{poly}"/>'
            )
            elems.append(
                f'<polyline class="wire-seg" data-net="{_esc(net)}" data-ref="{_esc(p.ref)}" '
                f'points="{poly}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0.55"/>'
            )
        elems.append(
            f'<text class="net-label lbl-net" data-net="{_esc(net)}" x="{cx:.1f}" y="{cy - 6:.1f}" '
            f'text-anchor="middle">{_esc(net)}</text>'
        )
        elems.append("</g>")
    return "\n".join(elems)


def render_alu8_schematic_svg(
    netlist: dict[str, Any],
    *,
    port_names: set[str] | None = None,
) -> tuple[str, float, float]:
    layout = layout_alu8_schematic(netlist, port_names=port_names)
    ports = port_names or set()
    port_labels = _port_label_positions(ports)

    wire_svg = _render_wires(layout.anchors, port_labels)
    sym_svg = "\n".join(_render_symbol(inst) for inst in layout.instances)
    label_svg = "\n".join(
        _render_global_label(net, x, y, side) for net, (x, y, side) in port_labels.items()
    )

    power_svg = ""
    if any(n["name"] in (PWR_VCC, PWR_GND) for n in netlist.get("nets", [])):
        power_svg = (
            f'<line class="pwr-rail" x1="{MARGIN:.1f}" y1="{MARGIN - 12:.1f}" '
            f'x2="{layout.width - MARGIN:.1f}" y2="{MARGIN - 12:.1f}" stroke="#f85149" stroke-width="1" opacity="0.4"/>'
            f'<text class="lbl-pwr" x="{MARGIN:.1f}" y="{MARGIN - 16:.1f}" fill="#f85149">VCC</text>'
            f'<line class="pwr-rail" x1="{MARGIN:.1f}" y1="{layout.height - MARGIN + 12:.1f}" '
            f'x2="{layout.width - MARGIN:.1f}" y2="{layout.height - MARGIN + 12:.1f}" stroke="#8b949e" stroke-width="1" opacity="0.4"/>'
            f'<text class="lbl-pwr" x="{MARGIN:.1f}" y="{layout.height - MARGIN + 24:.1f}" fill="#8b949e">GND</text>'
        )

    style = """
    svg{-webkit-user-select:none;user-select:none}
    text{font-family:system-ui,sans-serif;pointer-events:none;user-select:none}
    .lbl-ref{font-size:9px;font-weight:600;fill:#e6edf3}
    .lbl-part{font-size:7px;fill:#8b949e}
    .lbl-pin{font-size:7px;fill:#c9d1d9}
    .lbl-net{font-size:7px;fill:#8b949e;opacity:.85}
    .lbl-global{font-size:8px;font-weight:600}
    .wire-hit{fill:none;stroke:transparent;stroke-width:8;cursor:pointer}
    .net.highlight .wire-seg{stroke-width:2.2;opacity:1}
    .net.highlight .net-hub{r:5}
    .symbol.highlight .sym-body{stroke:#f0883e;stroke-width:2}
    """

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {layout.width:.0f} {layout.height:.0f}" '
        f'width="{layout.width:.0f}" height="{layout.height:.0f}">'
        f"<style>{style}</style>"
        f'<rect width="100%" height="100%" fill="#0d1117"/>'
        f"{power_svg}"
        f"{wire_svg}"
        f"{sym_svg}"
        f"{label_svg}"
        f"</svg>"
    )
    return svg, layout.width, layout.height


def net_anchor_map(layout: SchematicLayout) -> dict[str, list[PinAnchor]]:
    out: dict[str, list[PinAnchor]] = {}
    for a in layout.anchors:
        out.setdefault(a.net, []).append(a)
    return out
