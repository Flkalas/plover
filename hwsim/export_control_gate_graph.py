"""Stage-column gate connectivity graph for CPLD control research netlists."""

from __future__ import annotations

from collections import defaultdict

from hwsim.export_gate_schematic import _wire_color
from hwsim.export_schematic import PWR_GND, PWR_VCC, _esc
from hwsim.netlist import Netlist
from hwsim.units.catalog import ViewUnit
from hwsim.units.extract import extract_unit

STAGE_COL = 200.0
ROW_H = 96.0
MARGIN = 48.0
NODE_W = 120.0
NODE_H = 72.0

CONTROL_IO_PREFIXES = (
    "net_opc",
    "net_phase",
    "net_clk",
    "net_flg",
    "net_mem_",
    "net_reg_",
    "net_y_oe",
    "net_pc_load",
    "net_cin",
    "net_b_",
    "net_lgc",
    "net_y_mux",
)


def _is_control_io(net: str) -> bool:
    if net in (PWR_VCC, PWR_GND):
        return False
    return any(net.startswith(p) for p in CONTROL_IO_PREFIXES)


def _mini_symbol(kind: str, x: float, y: float) -> list[str]:
    cx = x + NODE_W / 2
    cy = y + NODE_H / 2
    if kind == "and_gate":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">&amp;</text>'
        ]
    if kind == "or_gate":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">OR</text>'
        ]
    if kind == "not_gate":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">NOT</text>'
        ]
    if kind in ("mux4_l", "mux2_addr", "mux2_y"):
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">MUX</text>'
        ]
    if kind == "counter4":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">161</text>'
        ]
    if kind == "latch8":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">574</text>'
        ]
    if kind == "decoder3x8":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">138</text>'
        ]
    if kind == "rom16":
        return [
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">Flash</text>'
        ]
    return [
        f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" class="sym">?</text>'
    ]


def export_control_gate_graph_svg(nl: Netlist, units: list[ViewUnit]) -> str:
    by_stage: dict[int, list[ViewUnit]] = defaultdict(list)
    for u in sorted(units, key=lambda x: (x.stage, x.id)):
        by_stage[u.stage].append(u)

    positions: dict[str, tuple[float, float]] = {}
    port_pos: dict[str, list[tuple[float, float]]] = defaultdict(list)

    max_rows = max(len(v) for v in by_stage.values()) if by_stage else 1
    width = MARGIN * 2 + len(by_stage) * STAGE_COL + 80
    height = MARGIN * 2 + max_rows * ROW_H + 40

    gate_elems: list[str] = []
    for stage, stage_units in sorted(by_stage.items()):
        col_x = MARGIN + (stage - 1) * STAGE_COL
        gate_elems.append(
            f'<text x="{col_x + NODE_W / 2:.1f}" y="{MARGIN - 16:.1f}" '
            f'text-anchor="middle" class="col-label">stage {stage}</text>'
        )
        for i, unit in enumerate(stage_units):
            y = MARGIN + i * ROW_H
            positions[unit.id] = (col_x, y)
            ex = extract_unit(nl, unit)
            gate_elems.append(
                f'<g class="gate-node" data-unit-id="{_esc(unit.id)}" '
                f'data-kind="{_esc(unit.kind)}" transform="translate({col_x:.1f},{y:.1f})">'
                f'<rect class="gate-body" width="{NODE_W:.1f}" height="{NODE_H:.1f}" rx="6" '
                f'fill="#21262d" stroke="#484f58" stroke-width="1.5"/>'
                f'<text x="{NODE_W / 2:.1f}" y="16" text-anchor="middle" class="node-label">'
                f'{_esc(unit.label)}</text>'
                f'<text x="{NODE_W / 2:.1f}" y="30" text-anchor="middle" class="node-kind">'
                f'{_esc(unit.kind)}</text>'
                + "".join(_mini_symbol(unit.kind, 0, 0))
                + "</g>"
            )
            left_x = col_x
            right_x = col_x + NODE_W
            cy = y + NODE_H / 2
            ins = [p for p in ex.boundary_ports if p.direction == "in"]
            outs = [p for p in ex.boundary_ports if p.direction == "out"]
            for j, p in enumerate(ins):
                py = y + 18 + j * 14
                port_pos[p.net].append((left_x, py))
            for j, p in enumerate(outs):
                py = y + 18 + j * 14
                port_pos[p.net].append((right_x, py))

    wire_elems: list[str] = []
    for net, pts in port_pos.items():
        if net in (PWR_VCC, PWR_GND) or len(pts) < 2:
            continue
        color = _wire_color(net)
        pts_sorted = sorted(pts, key=lambda t: (t[0], t[1]))
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_sorted)
        wire_elems.append(
            f'<polyline class="wire-seg" data-net="{_esc(net)}" points="{path}" '
            f'fill="none" stroke="{color}" stroke-width="1.4" opacity="0.75"/>'
        )

    io_elems: list[str] = []
    io_x = width - MARGIN - 20
    io_nets = sorted(n for n in port_pos if _is_control_io(n))
    for i, net in enumerate(io_nets):
        y = MARGIN + i * 18
        if not port_pos[net]:
            continue
        x0, y0 = port_pos[net][-1]
        io_elems.append(
            f'<g class="io-net" data-net="{_esc(net)}">'
            f'<line class="wire-seg" x1="{x0:.1f}" y1="{y0:.1f}" x2="{io_x:.1f}" y2="{y:.1f}" '
            f'stroke="{_wire_color(net)}" stroke-width="1.2"/>'
            f'<text x="{io_x + 6:.1f}" y="{y + 4:.1f}" class="io-label">{_esc(net.removeprefix("net_"))}</text>'
            f"</g>"
        )

    style = """
    text{font-family:system-ui,sans-serif;user-select:none}
    .title{font-size:14px;font-weight:600;fill:#e6edf3}
    .subtitle{font-size:10px;fill:#8b949e}
    .col-label{font-size:10px;fill:#6e7681;font-weight:600}
    .node-label{font-size:10px;font-weight:600;fill:#e6edf3}
    .node-kind{font-size:8px;fill:#6e7681}
    .sym{font-size:16px;font-weight:700;fill:#58a6ff}
    .io-label{font-size:8px;fill:#8b949e}
  """

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" data-gate-graph="1">',
        f"<style>{style}</style>",
        f'<text x="{MARGIN:.1f}" y="{MARGIN - 28:.1f}" class="title">{_esc(nl.block)} gate connectivity</text>',
        f'<text x="{MARGIN:.1f}" y="{MARGIN - 14:.1f}" class="subtitle">'
        f"{len(units)} units · stage columns</text>",
        '<g id="wires">',
        *wire_elems,
        "</g>",
        '<g id="io">',
        *io_elems,
        "</g>",
        '<g id="gates">',
        *gate_elems,
        "</g>",
        "</svg>",
    ]
    return "\n".join(lines)


def export_control_gate_graph_html(nl: Netlist, units: list[ViewUnit]) -> str:
    svg = export_control_gate_graph_svg(nl, units)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{_esc(nl.block)}</title>
<style>body{{margin:0;background:#0d1117}}#wrap{{overflow:auto}}</style></head>
<body><div id="wrap">{svg}</div></body></html>"""
