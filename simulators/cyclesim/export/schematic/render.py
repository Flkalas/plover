"""SVG rendering for ALU8 schematic."""

from __future__ import annotations

import hashlib
import html
from typing import Any

from simulators.cyclesim.export.schematic.alu8_template import (
    BUS_BOTTOM,
    BUS_CTRL_LEFT,
    BUS_TOP,
    GRID,
    ORPHAN_PORTS,
    PIN_LEN,
    Alu8Template,
    snap,
)
from simulators.cyclesim.export.schematic.symbols import PART_PINS, pin_position
from simulators.cyclesim.export.schematic.types import PinAnchor

PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"
MARGIN = 100.0
WIRE_OPACITY = 0.88
WIRE_WIDTH = 1.5
BEND_R = 2.8
ENDPOINT_R = 3.6

_LGC_COLORS = ("#58a6ff", "#3fb950", "#d29922", "#f85149")
_BCTRL_COLORS = ("#a371f7", "#db61a2", "#56d4dd", "#bc8cff")
_CTRL_LEFT_COLORS = {
    "net_cin": "#e3b341",
    "net_153_s0": "#f0883e",
    "net_153_s1": "#ff7b72",
    "net_y_mux_sel": "#ffa657",
}

_SIMPLE_NET = frozenset(
    {f"net_a{i}" for i in range(8)}
    | {f"net_b{i}" for i in range(8)}
    | {f"net_y{i}" for i in range(8)}
    | BUS_TOP
    | BUS_BOTTOM
    | BUS_CTRL_LEFT
    | {"net_y_mux_sel"}
    | ORPHAN_PORTS
)


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def net_stroke_color(net: str) -> str:
    if net in BUS_TOP:
        return _LGC_COLORS[int(net[-1])]
    if net in BUS_BOTTOM:
        return _BCTRL_COLORS[int(net[-1])]
    if net in _CTRL_LEFT_COLORS:
        return _CTRL_LEFT_COLORS[net]
    h = hashlib.md5(net.encode()).hexdigest()[:6]
    r = 80 + (int(h[0:2], 16) * 175) // 255
    g = 100 + (int(h[2:4], 16) * 155) // 255
    b = 120 + (int(h[4:6], 16) * 135) // 255
    return f"#{r:02x}{g:02x}{b:02x}"


def points_str(coords: list[tuple[float, float]]) -> str:
    return " ".join(f"{snap(x):.1f},{snap(y):.1f}" for x, y in coords)


def label_point(paths: list[list[tuple[float, float]]]) -> tuple[float, float]:
    if not paths:
        return 0.0, 0.0
    longest = max(
        paths,
        key=lambda p: sum(
            abs(p[i + 1][0] - p[i][0]) + abs(p[i + 1][1] - p[i][1]) for i in range(len(p) - 1)
        ),
    )
    return longest[0]


def render_grid(min_x: float, min_y: float, max_x: float, max_y: float) -> str:
    step = int(GRID)
    lines: list[str] = []
    x_start = int(snap(min_x))
    x_max = int(snap(max_x))
    y_start = int(snap(min_y))
    y_max = int(snap(max_y))
    x = x_start
    while x <= x_max:
        lines.append(
            f'<line x1="{x}" y1="{y_start}" x2="{x}" y2="{y_max}" '
            f'stroke="#21262d" stroke-width="0.5"/>'
        )
        x += step
    y = y_start
    while y <= y_max:
        lines.append(
            f'<line x1="{x_start}" y1="{y}" x2="{x_max}" y2="{y}" '
            f'stroke="#21262d" stroke-width="0.5"/>'
        )
        y += step
    return f'<g class="grid" opacity="0.45">{"".join(lines)}</g>'


def render_global_label(net: str, x: float, y: float, side: str, *, dashed: bool = False) -> str:
    color = net_stroke_color(net)
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    if side == "left":
        pts = (
            f"{x:.1f},{y:.1f} {x + 28:.1f},{y:.1f} {x + 28:.1f},{y - 10:.1f} "
            f"{x + 36:.1f},{y:.1f} {x + 28:.1f},{y + 10:.1f} {x + 28:.1f},{y:.1f}"
        )
        tx, anchor = x - 4, "end"
    else:
        pts = (
            f"{x:.1f},{y:.1f} {x - 28:.1f},{y:.1f} {x - 28:.1f},{y - 10:.1f} "
            f"{x - 36:.1f},{y:.1f} {x - 28:.1f},{y + 10:.1f} {x - 28:.1f},{y:.1f}"
        )
        tx, anchor = x + 4, "start"
    return (
        f'<g class="global-label" data-net="{_esc(net)}">'
        f'<polyline class="lbl-flag" points="{pts}" fill="{color}" opacity="0.35" '
        f'stroke="{color}" stroke-width="1"{dash}/>'
        f'<text class="net-label lbl-global" data-net="{_esc(net)}" x="{tx:.1f}" y="{y + 4:.1f}" '
        f'text-anchor="{anchor}" fill="{color}">{_esc(net)}</text>'
        f"</g>"
    )


def render_symbol(inst: dict[str, Any], tmpl: Alu8Template) -> str:
    ref = inst["ref"]
    part = inst["part"]
    ox, oy = inst["x"], inst["y"]
    body_w, body_h = inst["w"], inst["h"]
    lines = [
        f'<g class="symbol" data-ref="{_esc(ref)}">',
        f'<rect class="sym-body" x="{ox:.1f}" y="{oy:.1f}" width="{body_w:.1f}" height="{body_h:.1f}" '
        f'rx="2" fill="#161b22" stroke="#58a6ff" stroke-width="1.4"/>',
        f'<text class="lbl-ref" x="{ox + body_w / 2:.1f}" y="{oy + 12:.1f}" '
        f'text-anchor="middle">{_esc(ref)}</text>',
        f'<text class="lbl-part" x="{ox + body_w / 2:.1f}" y="{oy + body_h - 6:.1f}" '
        f'text-anchor="middle">{_esc(part)}</text>',
    ]
    for spec in PART_PINS[part]:
        px, py, side = pin_position(ref, part, spec, ox, oy, body_w, body_h, tmpl)
        if side == "left":
            x2 = px - PIN_LEN
            lx, anchor = px - PIN_LEN - 3, "end"
        elif side == "right":
            x2 = px + PIN_LEN
            lx, anchor = px + PIN_LEN + 3, "start"
        elif side == "top":
            y2 = py - PIN_LEN
            lines.append(
                f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{y2:.1f}" '
                f'stroke="#8b949e" stroke-width="1"/>'
            )
            lines.append(
                f'<text class="lbl-pin" x="{px:.1f}" y="{y2 - 3:.1f}" text-anchor="middle">'
                f"{_esc(spec.name)}</text>"
            )
            continue
        else:
            y2 = py + PIN_LEN
            lines.append(
                f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{y2:.1f}" '
                f'stroke="#8b949e" stroke-width="1"/>'
            )
            lines.append(
                f'<text class="lbl-pin" x="{px:.1f}" y="{y2 + 10:.1f}" text-anchor="middle">'
                f"{_esc(spec.name)}</text>"
            )
            continue
        lines.append(
            f'<line class="pin-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{x2:.1f}" y2="{py:.1f}" '
            f'stroke="#8b949e" stroke-width="1"/>'
        )
        lines.append(
            f'<text class="lbl-pin" x="{lx:.1f}" y="{py + 4:.1f}" text-anchor="{anchor}">'
            f"{_esc(spec.name)}</text>"
        )
    lines.append("</g>")
    return "\n".join(lines)


def render_path_nodes(
    path: list[tuple[float, float]],
    net: str,
    color: str,
    *,
    simple: bool,
) -> str:
    if len(path) < 1 or simple:
        return ""
    parts: list[str] = []
    for i, (x, y) in enumerate(path):
        if i == 0 or i == len(path) - 1:
            cls = "wire-endpoint"
            r = ENDPOINT_R
        else:
            cls = "wire-bend"
            r = BEND_R
        parts.append(
            f'<circle class="{cls}" data-net="{_esc(net)}" cx="{x:.1f}" cy="{y:.1f}" '
            f'r="{r:.1f}" fill="{color}" stroke="#0d1117" stroke-width="1.1" opacity="0.95"/>'
        )
    return "".join(parts)


def render_wires(
    routes: dict[str, list[list[tuple[float, float]]]],
    bus_rails: dict[str, float],
) -> str:
    elems: list[str] = []
    for net in sorted(routes):
        paths = routes[net]
        if not paths:
            continue
        color = net_stroke_color(net)
        simple = net in _SIMPLE_NET
        lx, ly = label_point(paths)
        elems.append(f'<g class="net" data-net="{_esc(net)}">')
        for path in paths:
            if len(path) < 2:
                continue
            poly = points_str(path)
            dash = ' stroke-dasharray="5 4"' if net in ORPHAN_PORTS else ""
            elems.append(f'<polyline class="wire-hit" data-net="{_esc(net)}" points="{poly}"/>')
            elems.append(
                f'<polyline class="wire-seg" data-net="{_esc(net)}" points="{poly}" '
                f'fill="none" stroke="{color}" stroke-width="{WIRE_WIDTH}" '
                f'opacity="{WIRE_OPACITY}"{dash}/>'
            )
            elems.append(render_path_nodes(path, net, color, simple=simple))
        if net in BUS_TOP | BUS_BOTTOM and paths:
            trunk = paths[0]
            if len(trunk) >= 2:
                x0, y0 = trunk[0]
                x1, y1 = trunk[1]
                elems.append(
                    f'<line class="bus-rail" data-net="{_esc(net)}" '
                    f'x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                    f'stroke="{color}" stroke-width="2.4" opacity="0.4"/>'
                )
        elif net in BUS_CTRL_LEFT or net == "net_y_mux_sel":
            rail_y = bus_rails.get(net)
            if rail_y is not None and paths:
                trunk = paths[0]
                if len(trunk) >= 2:
                    x0, y0 = trunk[0]
                    x1, y1 = trunk[1]
                    elems.append(
                        f'<line class="bus-rail" data-net="{_esc(net)}" '
                        f'x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                        f'stroke="{color}" stroke-width="2.4" opacity="0.4"/>'
                    )
        elems.append(
            f'<circle class="net-junction" data-net="{_esc(net)}" cx="{lx:.1f}" cy="{ly:.1f}" '
            f'r="2.5" fill="{color}" opacity="0.95"/>'
        )
        elems.append(
            f'<text class="net-label lbl-net" data-net="{_esc(net)}" x="{lx:.1f}" y="{ly - 8:.1f}" '
            f'text-anchor="middle">{_esc(net)}</text>'
        )
        elems.append("</g>")
    return "\n".join(elems)


def svg_styles() -> str:
    return """
    svg{-webkit-user-select:none;user-select:none}
    text{font-family:system-ui,sans-serif;pointer-events:none;user-select:none}
    .lbl-ref{font-size:9px;font-weight:600;fill:#e6edf3}
    .lbl-part{font-size:7px;fill:#8b949e}
    .lbl-pin{font-size:7px;fill:#c9d1d9}
    .lbl-net{font-size:7px;fill:#c9d1d9;opacity:.9}
    .lbl-global{font-size:8px;font-weight:600}
    .wire-hit{fill:none;stroke:transparent;stroke-width:12;cursor:pointer}
    .net.highlight .wire-seg{stroke-width:2.6;opacity:1}
    .net.highlight .bus-rail{opacity:0.75;stroke-width:3.2}
    .net.highlight .net-junction{r:4.5}
    .net.highlight .wire-bend{r:4.2}
    .net.highlight .wire-endpoint{r:5.2}
    .symbol.highlight .sym-body{stroke:#f0883e;stroke-width:2}
    """
