"""Export view-units as abstract logic-gate schematics (not DIP chips)."""

from __future__ import annotations

from hwsim.export_schematic import (
    _esc,
    _is_control_net,
    _net_color,
    export_schematic_html,
)
from hwsim.netlist import Netlist
from hwsim.units.catalog import ViewUnit
from hwsim.units.extract import UnitBoundaryPort, extract_unit

ROW = 22.0
MARGIN = 40.0
PORT_X = 24.0
GATE_X = 200.0
OUT_X = 360.0


def _wire_color(net: str) -> str:
    if _is_control_net(net):
        return "#d29922"
    return _net_color(net)


def _gate_title(unit: ViewUnit) -> str:
    titles = {
        "not_gate": "NOT",
        "mux4_b": "MUX 4:1",
        "mux4_l": "MUX 4:1",
        "adder4": "ADD 4-bit",
        "mux2_y": "MUX 2:1",
    }
    return titles.get(unit.kind, unit.kind)


def _gate_body_svg(kind: str, cx: float, cy: float) -> list[str]:
    """Logic symbol centered at (cx, cy)."""
    if kind == "not_gate":
        return [
            f'<path d="M{cx - 28:.1f},{cy:.1f} L{cx + 8:.1f},{cy - 18:.1f} '
            f'L{cx + 8:.1f},{cy + 18:.1f} Z" fill="#21262d" stroke="#58a6ff" stroke-width="2"/>',
            f'<circle cx="{cx + 16:.1f}" cy="{cy:.1f}" r="4" fill="none" stroke="#58a6ff" stroke-width="2"/>',
        ]
    if kind in ("mux4_b", "mux4_l"):
        return [
            f'<path d="M{cx - 32:.1f},{cy - 36:.1f} L{cx + 24:.1f},{cy - 20:.1f} '
            f'L{cx + 24:.1f},{cy + 20:.1f} L{cx - 32:.1f},{cy + 36:.1f} Z" '
            f'fill="#21262d" stroke="#a371f7" stroke-width="2"/>',
            f'<text x="{cx - 4:.1f}" y="{cy + 4:.1f}" text-anchor="middle" '
            f'class="gate-label">4:1</text>',
        ]
    if kind == "adder4":
        return [
            f'<rect x="{cx - 36:.1f}" y="{cy - 40:.1f}" width="72" height="80" rx="4" '
            f'fill="#21262d" stroke="#3fb950" stroke-width="2"/>',
            f'<text x="{cx:.1f}" y="{cy - 8:.1f}" text-anchor="middle" class="gate-label">+</text>',
            f'<text x="{cx:.1f}" y="{cy + 12:.1f}" text-anchor="middle" class="gate-sub">4-bit</text>',
        ]
    if kind == "mux2_y":
        return [
            f'<path d="M{cx - 28:.1f},{cy - 24:.1f} L{cx + 20:.1f},{cy - 12:.1f} '
            f'L{cx + 20:.1f},{cy + 12:.1f} L{cx - 28:.1f},{cy + 24:.1f} Z" '
            f'fill="#21262d" stroke="#d29922" stroke-width="2"/>',
            f'<text x="{cx - 4:.1f}" y="{cy + 4:.1f}" text-anchor="middle" class="gate-label">2:1</text>',
        ]
    return [
        f'<rect x="{cx - 30:.1f}" y="{cy - 20:.1f}" width="60" height="40" rx="4" '
        f'fill="#21262d" stroke="#8b949e" stroke-width="2"/>',
    ]


def _layout_ports(ports: list[UnitBoundaryPort]) -> tuple[list[UnitBoundaryPort], list[UnitBoundaryPort]]:
    ins = [p for p in ports if p.direction == "in"]
    outs = [p for p in ports if p.direction == "out"]
    return ins, outs


def export_gate_schematic_svg(nl: Netlist, unit: ViewUnit) -> str:
    extracted = extract_unit(nl, unit)
    ports = extracted.boundary_ports
    ins, outs = _layout_ports(ports)
    n_rows = max(len(ins), len(outs), 1)
    height = MARGIN * 2 + n_rows * ROW + 20
    width = OUT_X + MARGIN + 40
    gate_cy = MARGIN + (n_rows - 1) * ROW / 2 + 10

    elems: list[str] = []
    wire_elems: list[str] = []

    def port_y(index: int, total: int) -> float:
        if total <= 1:
            return gate_cy
        span = (total - 1) * ROW
        return gate_cy - span / 2 + index * ROW

    gate_in_x = GATE_X - 32
    gate_out_x = GATE_X + (16 if unit.kind == "not_gate" else 24)

    for i, port in enumerate(ins):
        y = port_y(i, len(ins))
        color = _wire_color(port.net)
        wire_elems.append(
            f'<polyline class="wire-seg" data-net="{_esc(port.net)}" '
            f'points="{PORT_X + 50:.1f},{y:.1f} {gate_in_x:.1f},{y:.1f} {gate_in_x:.1f},{gate_cy:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="1.5" opacity="0.8"/>'
        )
        elems.append(
            f'<g class="port in" data-net="{_esc(port.net)}">'
            f'<circle cx="{PORT_X + 50:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>'
            f'<text x="{PORT_X:.1f}" y="{y + 4:.1f}" class="port-label">{_esc(port.label)}</text>'
            f'<text x="{PORT_X + 58:.1f}" y="{y + 4:.1f}" class="pin-label">{_esc(port.logical_pin)}</text>'
            f"</g>"
        )

    for i, port in enumerate(outs):
        y = port_y(i, len(outs))
        color = _wire_color(port.net)
        wire_elems.append(
            f'<polyline class="wire-seg" data-net="{_esc(port.net)}" '
            f'points="{gate_out_x:.1f},{gate_cy:.1f} {gate_out_x:.1f},{y:.1f} {OUT_X - 10:.1f},{y:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="1.5" opacity="0.8"/>'
        )
        elems.append(
            f'<g class="port out" data-net="{_esc(port.net)}">'
            f'<circle cx="{OUT_X - 10:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>'
            f'<text x="{OUT_X:.1f}" y="{y + 4:.1f}" class="port-label">{_esc(port.label)}</text>'
            f'<text x="{OUT_X - 18:.1f}" y="{y + 4:.1f}" text-anchor="end" class="pin-label">'
            f'{_esc(port.logical_pin)}</text>'
            f"</g>"
        )

    style = """
    text{font-family:system-ui,sans-serif;user-select:none}
    .title{font-size:13px;font-weight:600;fill:#e6edf3}
    .subtitle{font-size:10px;fill:#8b949e}
    .gate-label{font-size:14px;font-weight:700;fill:#e6edf3}
    .gate-sub{font-size:9px;fill:#8b949e}
    .port-label{font-size:11px;fill:#c9d1d9}
    .pin-label{font-size:9px;fill:#8b949e}
    .col-hdr{font-size:9px;fill:#6e7681;text-transform:uppercase}
    """

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" data-unit-id="{_esc(unit.id)}" '
        f'data-gate-view="1">',
        f"<style>{style}</style>",
        f'<text x="{MARGIN:.1f}" y="{MARGIN - 12:.1f}" class="title">{_esc(unit.label)}</text>',
        f'<text x="{MARGIN:.1f}" y="{MARGIN:.1f}" class="subtitle">{_esc(_gate_title(unit))} · {_esc(unit.id)}</text>',
        f'<text x="{PORT_X:.1f}" y="{MARGIN + 8:.1f}" class="col-hdr">in</text>',
        f'<text x="{OUT_X:.1f}" y="{MARGIN + 8:.1f}" class="col-hdr">out</text>',
        '<g id="gate">',
        *_gate_body_svg(unit.kind, GATE_X, gate_cy),
        "</g>",
        '<g id="wires">',
        *wire_elems,
        "</g>",
        '<g id="ports">',
        *elems,
        "</g>",
        "</svg>",
    ]
    return "\n".join(lines)


def export_gate_schematic_html(nl: Netlist, unit: ViewUnit) -> str:
    svg = export_gate_schematic_svg(nl, unit)
    title = f"ALU8 gate: {unit.label}"
    return export_schematic_html(svg, title=title)
