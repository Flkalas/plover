"""Export full ALU8 gate-level connectivity schematic."""

from __future__ import annotations

from dataclasses import dataclass

from hwsim.export_schematic import PWR_GND, PWR_VCC, _esc, _is_control_net
from hwsim.export_gate_schematic import _gate_title, _wire_color
from hwsim.netlist import Netlist
from hwsim.units.catalog import ViewUnit, load_alu8_catalog
from hwsim.units.extract import FixedPort, UnitExtract, extract_unit
from hwsim.units.gate_graph import (
    build_gate_graph,
    is_a_operand_bit_net,
    is_b_operand_bit_net,
    is_external_net,
)
from hwsim.wiring.gate_branch import Anchor, BranchNet, fmt_path, layout_branch_net

MARGIN = 48.0
NODE_W = 58.0
NODE_H = 104.0
GATE_GAP = 48.0  # vertical space between gate boxes (ROW must exceed NODE_H)
ROW = NODE_H + GATE_GAP
ROW0 = 72.0
ADD_H = 168.0
CTRL_IO_MARGIN = 44.0
SIDE_STUB = 14.0
CHANNEL_STEP = 10.0
BOTTOM_STUB = 20.0
BOTTOM_STUB_STEP = 10.0
CONST_STUB = 20.0
PORT_R = 3.0
FIXED_PORT_COLOR = "#484f58"

COL = {
    "io_in": 80.0,
    "not_gate": 220.0,
    "mux4_b": 400.0,
    "mux4_bit": 580.0,
    "adder4": 580.0,
    "mux4_l": 760.0,
    "mux2_y": 940.0,
    "io_out": 1100.0,
}

# 74HC153 data inputs: netlist uses C0..C3 or 1C0..2C3; display as D0..D3
_HC153_DATA_PIN = {"C0": "D0", "C1": "D1", "C2": "D2", "C3": "D3"}
for _mux in ("1", "2"):
    for _i in range(4):
        _HC153_DATA_PIN[f"{_mux}C{_i}"] = f"D{_i}"

_MUX4_BIT_LEFT_ORDER = ("1C0", "1C1", "1C2", "1C3", "2C0", "2C1", "2C2", "2C3")
_MUX4_BIT_BOTTOM_ORDER = ("A", "B", "1G", "2G")


@dataclass
class NodeLayout:
    unit_id: str
    kind: str
    label: str
    x: float
    y: float
    w: float
    h: float
    in_nets: list[str]
    out_nets: list[str]
    fixed_ports: list[FixedPort]


@dataclass(frozen=True)
class _PortSlot:
    kind: str  # net | fixed
    logical: str
    net: str = ""
    value: str = ""


def _bit_index(unit: ViewUnit) -> int | None:
    if unit.kind == "not_gate":
        return int(unit.id.split("_")[1])
    if unit.kind == "mux4_l":
        return int(unit.id.split("_")[-1])
    if unit.kind == "mux4_bit":
        return int(unit.id.split("_")[-1])
    if unit.kind == "mux2_y":
        return int(unit.id.split("_")[-1])
    if unit.kind == "mux4_b":
        parts = unit.id.split("_")
        chip, mux = int(parts[2]), int(parts[3])
        return chip * 2 + (mux - 1)
    return None


def _layout_nodes(units: list[ViewUnit], nl: Netlist) -> list[NodeLayout]:
    nodes: list[NodeLayout] = []
    for unit in units:
        ex = extract_unit(nl, unit)
        ins = [p.net for p in ex.boundary_ports if p.direction == "in"]
        outs = [p.net for p in ex.boundary_ports if p.direction == "out"]
        bit = _bit_index(unit)
        if unit.kind == "adder4":
            x = COL["adder4"]
            if unit.id == "283_lo":
                y = ROW0 + 1.5 * ROW
                h = ADD_H
            else:
                y = ROW0 + 5.5 * ROW
                h = ADD_H
            nodes.append(
                NodeLayout(unit.id, unit.kind, unit.label, x, y, NODE_W, h, ins, outs, ex.fixed_ports)
            )
            continue
        col = COL.get(unit.kind, COL["mux4_l"])
        row = bit if bit is not None else 0
        y = ROW0 + row * ROW
        nodes.append(
            NodeLayout(
                unit.id, unit.kind, unit.label, col, y, NODE_W, NODE_H, ins, outs, ex.fixed_ports
            )
        )
    return nodes


def _logical_by_net(ex: UnitExtract) -> dict[str, str]:
    return {p.net: p.logical_pin for p in ex.boundary_ports}


def _pin_description(kind: str, logical: str) -> str:
    """IC pin name for schematic label (not net or ALU purpose name)."""
    if not logical:
        return ""
    if kind in ("mux4_b", "mux4_l", "mux4_bit") and logical in _HC153_DATA_PIN:
        return _HC153_DATA_PIN[logical]
    return logical


def _render_pin_label(side: str, px: float, py: float, desc: str) -> str:
    if not desc:
        return ""
    if side == "left":
        return (
            f'<text x="{px - 6:.1f}" y="{py + 4:.1f}" text-anchor="end" class="pin-desc">'
            f"{_esc(desc)}</text>"
        )
    if side == "right":
        return (
            f'<text x="{px + 6:.1f}" y="{py + 4:.1f}" text-anchor="start" class="pin-desc">'
            f"{_esc(desc)}</text>"
        )
    return (
        f'<text x="{px:.1f}" y="{py + 14:.1f}" text-anchor="middle" class="pin-desc">'
        f"{_esc(desc)}</text>"
    )


def _short_label(unit: ViewUnit) -> str:
    bit = _bit_index(unit)
    if unit.kind == "not_gate":
        return f"~B{bit}"
    if unit.kind == "mux4_b":
        return f"B{bit}"
    if unit.kind in ("mux4_l", "mux4_bit"):
        return f"L{bit}" if unit.kind == "mux4_l" else f"153{bit}"
    if unit.kind == "mux2_y":
        return f"Y{bit}"
    if unit.id == "283_lo":
        return "+LO"
    if unit.id == "283_hi":
        return "+HI"
    return unit.id


def _route_x_left(node: NodeLayout, index: int) -> float:
    return node.x - SIDE_STUB - index * CHANNEL_STEP


def _route_x_right(node: NodeLayout, index: int) -> float:
    return node.x + node.w + SIDE_STUB + index * CHANNEL_STEP


def _route_x_bottom(node: NodeLayout, index: int, total: int) -> float:
    mid = node.x + node.w / 2
    return mid - (total - 1) * CHANNEL_STEP / 2 + index * CHANNEL_STEP


def _render_branch_net(net: str, branch: BranchNet, color: str, ctrl: bool) -> list[str]:
    sw = 1.8 if ctrl else 1.3
    trunk_sw = sw
    elems = [
        f'<g class="net" data-net="{_esc(net)}" data-topology="{_esc(branch.topology)}">',
    ]
    if branch.hub:
        hx, hy = branch.hub
        elems.append(
            f'<circle class="net-hub" data-net="{_esc(net)}" cx="{hx:.1f}" cy="{hy:.1f}" '
            f'r="3" fill="{color}" opacity="0.9"/>'
        )
    for jx, jy, uid in branch.junctions:
        if uid == "hub":
            continue
        elems.append(
            f'<circle class="net-junction" data-net="{_esc(net)}" data-end="{_esc(uid)}" '
            f'cx="{jx:.1f}" cy="{jy:.1f}" r="2.5" fill="{color}" opacity="0.85"/>'
        )
    for seg in branch.segments:
        pts = fmt_path(seg.points)
        if not pts:
            continue
        cls = "wire-trunk" if seg.role == "trunk" else "wire-seg"
        end_attr = f' data-end="{_esc(seg.endpoint)}"' if seg.endpoint else ""
        opacity = "0.8" if cls == "wire-trunk" else "0.65"
        elems.append(
            f'<polyline class="{cls}" data-net="{_esc(net)}"{end_attr} points="{pts}" '
            f'fill="none" stroke="{color}" stroke-width="{trunk_sw if cls == "wire-trunk" else sw}" '
            f'opacity="{opacity}" pointer-events="none"/>'
        )
        elems.append(
            f'<polyline class="wire-hit" data-net="{_esc(net)}"{end_attr} data-role="{seg.role}" '
            f'points="{pts}" fill="none" stroke="transparent" stroke-width="14"/>'
        )
    elems.append("</g>")
    return elems


def _mini_gate_svg(kind: str, x: float, y: float, w: float, h: float) -> list[str]:
    cy = y + h / 2
    if kind == "not_gate":
        sym_h = min(h * 0.44, 44.0)
        left = x + 9.0
        tip = x + w - 18.0
        bubble = x + w - 10.0
        return [
            f'<path class="gate-symbol" pointer-events="none" '
            f'd="M{left:.1f},{cy - sym_h / 2:.1f} L{tip:.1f},{cy:.1f} '
            f'L{left:.1f},{cy + sym_h / 2:.1f} Z" fill="#21262d" stroke="#58a6ff" stroke-width="1.5"/>',
            f'<line class="gate-symbol" pointer-events="none" x1="{tip:.1f}" y1="{cy:.1f}" '
            f'x2="{bubble - 3.5:.1f}" y2="{cy:.1f}" stroke="#58a6ff" stroke-width="1.5"/>',
            f'<circle class="gate-symbol" pointer-events="none" cx="{bubble:.1f}" cy="{cy:.1f}" '
            f'r="3.5" fill="#161b22" stroke="#58a6ff" stroke-width="1.5"/>',
        ]
    if kind in ("mux4_b", "mux4_l"):
        return [
            f'<path class="gate-symbol" pointer-events="none" d="M{x + 6:.1f},{y + 4:.1f} '
            f'L{x + w - 10:.1f},{y + h * 0.35:.1f} L{x + w - 10:.1f},{y + h * 0.65:.1f} '
            f'L{x + 6:.1f},{y + h - 4:.1f} Z" fill="#21262d" stroke="#a371f7" stroke-width="1.5"/>',
        ]
    if kind == "adder4":
        return [
            f'<rect class="gate-symbol" pointer-events="none" x="{x + 6:.1f}" y="{y + 4:.1f}" '
            f'width="{w - 12:.1f}" height="{h - 8:.1f}" rx="3" fill="#21262d" stroke="#3fb950" '
            f'stroke-width="1.5"/>',
            f'<text class="gate-symbol mini-gate" pointer-events="none" x="{x + w / 2:.1f}" '
            f'y="{y + h / 2 + 4:.1f}" text-anchor="middle">+4</text>',
        ]
    if kind == "mux2_y":
        return [
            f'<path class="gate-symbol" pointer-events="none" d="M{x + 6:.1f},{y + 5:.1f} '
            f'L{x + w - 8:.1f},{y + h * 0.38:.1f} L{x + w - 8:.1f},{y + h * 0.62:.1f} '
            f'L{x + 6:.1f},{y + h - 5:.1f} Z" fill="#21262d" stroke="#d29922" stroke-width="1.5"/>',
        ]
    return [
        f'<rect class="gate-symbol" pointer-events="none" x="{x + 6:.1f}" y="{y + 4:.1f}" '
        f'width="{w - 12:.1f}" height="{h - 8:.1f}" rx="3" fill="#21262d" stroke="#8b949e" '
        f'stroke-width="1.5"/>',
    ]


def _in_by_logical(ex: UnitExtract) -> dict[str, str]:
    return {
        bp.logical_pin: bp.net
        for bp in ex.boundary_ports
        if bp.direction == "in"
    }


def _fixed_by_logical(ex: UnitExtract) -> dict[str, str]:
    return {fp.logical_pin: fp.value for fp in ex.fixed_ports}


def _left_port_slots(ex: UnitExtract, left_nets: list[str]) -> list[_PortSlot]:
    """Left-edge ports in IC pin order; fixed ties fill missing data inputs."""
    net_by = _in_by_logical(ex)
    fixed_by = _fixed_by_logical(ex)
    left_set = set(left_nets)

    if ex.unit.kind in ("mux4_b", "mux4_l"):
        slots: list[_PortSlot] = []
        for logical in ("C0", "C1", "C2", "C3"):
            if logical in net_by and net_by[logical] in left_set:
                slots.append(_PortSlot("net", logical, net=net_by[logical]))
            elif logical in fixed_by:
                slots.append(_PortSlot("fixed", logical, value=fixed_by[logical]))
        return slots

    if ex.unit.kind == "mux4_bit":
        slots = []
        for logical in _MUX4_BIT_LEFT_ORDER:
            if logical in net_by and net_by[logical] in left_set:
                slots.append(_PortSlot("net", logical, net=net_by[logical]))
            elif logical in fixed_by:
                slots.append(_PortSlot("fixed", logical, value=fixed_by[logical]))
        return slots

    slots = []
    for net in _sort_left_ins(left_nets):
        logical = next(
            (bp.logical_pin for bp in ex.boundary_ports if bp.net == net and bp.direction == "in"),
            "",
        )
        slots.append(_PortSlot("net", logical, net=net))
    return slots


def _bottom_port_slots(ex: UnitExtract, bottom_nets: list[str]) -> list[_PortSlot]:
    """Bottom-edge selects and enables; fixed ties appended in IC pin order."""
    net_by = _in_by_logical(ex)
    fixed_by = _fixed_by_logical(ex)
    bottom_set = set(bottom_nets)

    order: tuple[str, ...] | None
    if ex.unit.kind in ("mux4_b", "mux4_l"):
        order = ("A", "B", "G")
    elif ex.unit.kind == "mux4_bit":
        order = _MUX4_BIT_BOTTOM_ORDER
    elif ex.unit.kind == "mux2_y":
        order = ("S", "OE")
    else:
        order = None

    if order is None:
        return [
            _PortSlot(
                "net",
                next(
                    (bp.logical_pin for bp in ex.boundary_ports if bp.net == net and bp.direction == "in"),
                    "",
                ),
                net=net,
            )
            for net in bottom_nets
        ]

    slots: list[_PortSlot] = []
    for logical in order:
        if logical in net_by and net_by[logical] in bottom_set:
            slots.append(_PortSlot("net", logical, net=net_by[logical]))
        elif logical in fixed_by:
            slots.append(_PortSlot("fixed", logical, value=fixed_by[logical]))
    return slots


def _render_fixed_bottom_port(
    node: NodeLayout,
    index: int,
    total: int,
    logical: str,
    value: str,
) -> str:
    px = _port_x_bottom(node, index, total)
    py = node.y + node.h
    stub_y = _bottom_stub_y(py, index)
    stub_tip_y = py + CONST_STUB
    desc = _pin_description(node.kind, logical)
    return (
        f'<g class="port-fixed" data-unit="{_esc(node.unit_id)}" data-logical="{_esc(logical)}" '
        f'data-value="{value}">'
        f'<line class="const-stub" x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{stub_tip_y:.1f}" '
        f'stroke="{FIXED_PORT_COLOR}" stroke-width="1.2"/>'
        f'<text x="{px:.1f}" y="{stub_tip_y + 10:.1f}" text-anchor="middle" class="const-label">'
        f'{value}</text>'
        f'{_render_pin_label("bottom", px, py, desc)}'
        f'<circle class="port in bottom fixed" data-port-side="bottom" data-logical="{_esc(logical)}" '
        f'data-stub-y="{stub_y:.1f}" cx="{px:.1f}" cy="{py:.1f}" r="{PORT_R:.1f}" '
        f'fill="{FIXED_PORT_COLOR}"/>'
        f"</g>"
    )


def _render_fixed_left_port(
    node: NodeLayout,
    index: int,
    total: int,
    bottom_count: int,
    logical: str,
    value: str,
) -> str:
    py = _port_y_side(node, index, total, bottom_count=bottom_count)
    px = node.x
    stub_x = px - CONST_STUB
    desc = _pin_description(node.kind, logical)
    return (
        f'<g class="port-fixed" data-unit="{_esc(node.unit_id)}" data-logical="{_esc(logical)}" '
        f'data-value="{value}">'
        f'<line class="const-stub" x1="{stub_x:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
        f'stroke="{FIXED_PORT_COLOR}" stroke-width="1.2"/>'
        f'<text x="{stub_x - 4:.1f}" y="{py + 3:.1f}" text-anchor="end" class="const-label">'
        f'{value}</text>'
        f'{_render_pin_label("left", px, py, desc)}'
        f'<circle class="port in fixed" data-port-side="left" cx="{px:.1f}" cy="{py:.1f}" r="{PORT_R:.1f}" '
        f'fill="{FIXED_PORT_COLOR}"/>'
        f"</g>"
    )


def _split_inputs(in_nets: list[str]) -> tuple[list[str], list[str]]:
    """Data-path inputs on the left; decode/control selects on the bottom."""
    left: list[str] = []
    bottom: list[str] = []
    for net in in_nets:
        if _is_control_net(net):
            bottom.append(net)
        else:
            left.append(net)
    return left, bottom


def _split_inputs_for_unit(ex: UnitExtract, in_nets: list[str]) -> tuple[list[str], list[str]]:
    """153 4:1 mux: C0..C3 data on left, A/B select (+ fixed G) on bottom."""
    if ex.unit.kind in ("mux4_b", "mux4_l"):
        in_set = set(in_nets)
        net_by = _in_by_logical(ex)
        left = [net_by[p] for p in ("C0", "C1", "C2", "C3") if p in net_by and net_by[p] in in_set]
        bottom = [net_by[p] for p in ("A", "B") if p in net_by and net_by[p] in in_set]
        return left, bottom
    if ex.unit.kind == "mux4_bit":
        in_set = set(in_nets)
        net_by = _in_by_logical(ex)
        left = [net_by[p] for p in _MUX4_BIT_LEFT_ORDER if p in net_by and net_by[p] in in_set]
        bottom = [net_by[p] for p in ("A", "B") if p in net_by and net_by[p] in in_set]
        return left, bottom
    return _split_inputs(in_nets)


def _sort_left_ins(nets: list[str]) -> list[str]:
    """Operand nets first, then ~B / other data, so ports stack predictably."""

    def order(n: str) -> tuple[int, str]:
        if n.startswith("net_b_inv") or n.startswith("net_a_inv"):
            return (2, n)
        if is_b_operand_bit_net(n) or is_a_operand_bit_net(n):
            return (0, n)
        return (1, n)

    return sorted(nets, key=order)


def _port_y_side(node: NodeLayout, index: int, total: int, *, bottom_count: int) -> float:
    if total <= 1:
        cy = node.y + node.h * (0.42 if bottom_count else 0.5)
        return cy
    pad = 14.0
    bottom_reserve = 20.0 if bottom_count else 0.0
    top = node.y + pad
    bottom = node.y + node.h - pad - bottom_reserve
    span = max(bottom - top, 1.0)
    return top + span * index / (total - 1)


def _port_x_bottom(node: NodeLayout, index: int, total: int) -> float:
    if total <= 1:
        return node.x + node.w / 2
    pad = 8.0
    span = node.w - 2 * pad
    return node.x + pad + span * index / (total - 1)


def _bottom_stub_y(py: float, index: int) -> float:
    """Unique horizontal bend Y per bottom port on the same gate edge."""
    return py + BOTTOM_STUB + index * BOTTOM_STUB_STEP


def _port_y(node: NodeLayout, index: int, total: int) -> float:
    return _port_y_side(node, index, total, bottom_count=0)


def export_gate_graph_svg(nl: Netlist, units: list[ViewUnit] | None = None) -> str:
    units = units or load_alu8_catalog()
    graph = build_gate_graph(nl, units)
    nodes = _layout_nodes(units, nl)
    node_by_id = {n.unit_id: n for n in nodes}

    width = COL["io_out"] + MARGIN + 32.0
    height = ROW0 + 8 * ROW + MARGIN + CTRL_IO_MARGIN
    ctrl_io_y = height - CTRL_IO_MARGIN + 16.0

    # net -> Anchor list (port_x, port_y, unit_id, side, route_x, stub_y)
    anchors: dict[str, list[Anchor]] = {}

    gate_elems: list[str] = []
    for node in nodes:
        unit = graph.units[node.unit_id]
        gate_elems.append(
            f'<g class="gate-node" data-unit-id="{_esc(node.unit_id)}" data-kind="{_esc(node.kind)}" '
            f'transform="translate(0,0)" style="cursor:grab">'
            f'<rect class="gate-body" x="{node.x:.1f}" y="{node.y:.1f}" width="{node.w:.1f}" height="{node.h:.1f}" '
            f'rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>'
        )
        gate_elems.extend(_mini_gate_svg(node.kind, node.x, node.y, node.w, node.h))
        gate_elems.append(
            f'<text x="{node.x + node.w / 2:.1f}" y="{node.y + 14:.1f}" text-anchor="middle" '
            f'class="node-label" pointer-events="none">{_esc(_short_label(unit))}</text>'
        )
        gate_elems.append(
            f'<text x="{node.x + node.w / 2:.1f}" y="{node.y + node.h - 8:.1f}" text-anchor="middle" '
            f'class="node-kind" pointer-events="none">{_esc(_gate_title(unit))}</text>'
        )

        ex = extract_unit(nl, unit)
        logical_map = _logical_by_net(ex)
        left_ins, bottom_ins = _split_inputs_for_unit(ex, node.in_nets)
        left_slots = _left_port_slots(ex, left_ins)
        bottom_slots = _bottom_port_slots(ex, bottom_ins)
        bottom_count = len(bottom_slots)

        for i, slot in enumerate(left_slots):
            if slot.kind == "net":
                py = _port_y_side(node, i, len(left_slots), bottom_count=bottom_count)
                px = node.x
                rx = _route_x_left(node, i)
                color = _wire_color(slot.net)
                desc = _pin_description(node.kind, slot.logical)
                gate_elems.append(
                    f'<g class="port-group" data-net="{_esc(slot.net)}">'
                    f'{_render_pin_label("left", px, py, desc)}'
                    f'<circle class="port in" data-port-side="left" data-net="{_esc(slot.net)}" '
                    f'data-unit="{_esc(node.unit_id)}" data-logical="{_esc(slot.logical)}" '
                    f'data-pin-desc="{_esc(desc)}" data-route-x="{rx:.1f}" '
                    f'cx="{px:.1f}" cy="{py:.1f}" r="{PORT_R:.1f}" fill="{color}"/>'
                    f"</g>"
                )
                anchors.setdefault(slot.net, []).append(
                    (px, py, node.unit_id, "left", rx, py)
                )
            else:
                gate_elems.append(
                    _render_fixed_left_port(
                        node, i, len(left_slots), bottom_count, slot.logical, slot.value
                    )
                )

        for i, slot in enumerate(bottom_slots):
            if slot.kind == "net":
                px = _port_x_bottom(node, i, bottom_count)
                py = node.y + node.h
                rx = _route_x_bottom(node, i, bottom_count)
                stub_y = _bottom_stub_y(py, i)
                desc = _pin_description(node.kind, slot.logical)
                gate_elems.append(
                    f'<g class="port-group" data-net="{_esc(slot.net)}">'
                    f'{_render_pin_label("bottom", px, py, desc)}'
                    f'<circle class="port in bottom" data-port-side="bottom" data-net="{_esc(slot.net)}" '
                    f'data-unit="{_esc(node.unit_id)}" data-logical="{_esc(slot.logical)}" '
                    f'data-pin-desc="{_esc(desc)}" data-route-x="{rx:.1f}" '
                    f'data-stub-y="{stub_y:.1f}" '
                    f'cx="{px:.1f}" cy="{py:.1f}" r="{PORT_R:.1f}" fill="{_wire_color(slot.net)}"/>'
                    f"</g>"
                )
                anchors.setdefault(slot.net, []).append((px, py, node.unit_id, "bottom", rx, stub_y))
            else:
                gate_elems.append(
                    _render_fixed_bottom_port(node, i, bottom_count, slot.logical, slot.value)
                )

        for i, net in enumerate(node.out_nets):
            py = _port_y(node, i, len(node.out_nets))
            px = node.x + node.w
            rx = _route_x_right(node, i)
            logical = logical_map.get(net, "")
            desc = _pin_description(node.kind, logical)
            gate_elems.append(
                f'<g class="port-group" data-net="{_esc(net)}">'
                f'{_render_pin_label("right", px, py, desc)}'
                f'<circle class="port out" data-port-side="right" data-net="{_esc(net)}" '
                f'data-unit="{_esc(node.unit_id)}" data-logical="{_esc(logical)}" '
                f'data-pin-desc="{_esc(desc)}" data-route-x="{rx:.1f}" '
                f'cx="{px:.1f}" cy="{py:.1f}" r="{PORT_R:.1f}" fill="{_wire_color(net)}"/>'
                f"</g>"
            )
            anchors.setdefault(net, []).append((px, py, node.unit_id, "right", rx, py))

        gate_elems.append("</g>")

    io_elems: list[str] = []
    for net, plist in sorted(graph.net_to_ports.items()):
        if not is_external_net(net):
            continue
        pts = anchors.get(net, [])
        if not pts:
            continue
        # IO stub on left for inputs, right for outputs
        outs = [p for p in plist if p.direction == "out"]
        ins = [p for p in plist if p.direction == "in"]
        color = _wire_color(net)
        short = net.removeprefix("net_")
        if _is_control_net(net):
            gate_pts = [p for p in pts if p[3] != "io"]
            gx = sum(p[0] for p in gate_pts) / len(gate_pts) if gate_pts else COL["mux4_b"]
            gy = ctrl_io_y
            text_anchor = "middle"
            tx = gx
            ty = gy + 12.0
        elif ins and not outs:
            gx = COL["io_in"]
            gy = sum(p[1] for p in pts) / len(pts)
            text_anchor = "start"
            tx = gx + 8
            ty = gy + 3
        elif outs and not ins:
            gx = COL["io_out"]
            gy = sum(p[1] for p in pts) / len(pts)
            text_anchor = "end"
            tx = gx - 8
            ty = gy + 3
        else:
            gx = COL["io_in"] if net.startswith("net_a") or net.startswith("net_b") else COL["io_out"]
            gy = sum(p[1] for p in pts) / len(pts)
            text_anchor = "start" if gx < 400 else "end"
            tx = gx + (8 if gx < 400 else -8)
            ty = gy + 3
        io_elems.append(
            f'<g class="io-net{" ctrl" if _is_control_net(net) else ""}" data-net="{_esc(net)}">'
            f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="3" fill="{color}"/>'
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{text_anchor}" class="io-label">'
            f'{_esc(short)}</text>'
            f"</g>"
        )
        anchors.setdefault(net, []).append((gx, gy, "io", "io", gx, gy))

    wire_elems: list[str] = []
    for net, pts in anchors.items():
        if net in (PWR_VCC, PWR_GND):
            continue
        if len(pts) < 2:
            continue
        branch = layout_branch_net(pts, net)
        if not branch.segments:
            continue
        color = _wire_color(net)
        ctrl = _is_control_net(net)
        wire_elems.extend(_render_branch_net(net, branch, color, ctrl))

    col_labels = [
        (COL["not_gate"], "NOT"),
        (COL["mux4_b"], "MUX B"),
        (COL["adder4"], "ADD"),
        (COL["mux4_l"], "MUX L"),
        (COL["mux2_y"], "MUX Y"),
    ]
    header_elems = [
        f'<text x="{MARGIN:.1f}" y="{MARGIN - 8:.1f}" class="title">ALU8 gate connectivity</text>',
        f'<text x="{MARGIN:.1f}" y="{MARGIN + 6:.1f}" class="subtitle">'
        f'{len(units)} gates · logic view (not DIP)</text>',
    ]
    for cx, title in col_labels:
        header_elems.append(
            f'<text x="{cx + NODE_W / 2:.1f}" y="{ROW0 - 14:.1f}" text-anchor="middle" '
            f'class="col-label">{title}</text>'
        )

    style = """
    text{font-family:system-ui,sans-serif;user-select:none}
    .title{font-size:14px;font-weight:600;fill:#e6edf3}
    .subtitle{font-size:10px;fill:#8b949e}
    .col-label{font-size:11px;fill:#6e7681;font-weight:600}
    .node-label{font-size:11px;font-weight:600;fill:#e6edf3}
    .node-kind{font-size:9px;fill:#6e7681}
    .pin-desc{font-size:8px;fill:#c9d1d9;font-weight:500}
    .mini-gate{font-size:12px;font-weight:700;fill:#3fb950}
    .io-label{font-size:9px;fill:#8b949e}
    .wire-hit{fill:none;stroke:transparent;stroke-width:14;cursor:move}
    .wire-trunk{pointer-events:none}
    .net-hub,.net-junction{cursor:move;stroke:none}
    .net-junction{stroke:#0d1117;stroke-width:0.5}
    .gate-node{cursor:grab}
    .gate-node:active{cursor:grabbing}
    .gate-body{cursor:grab}
    .gate-symbol,.node-label,.node-kind{pointer-events:none}
    .io-net{cursor:move}
    .io-net.ctrl circle{stroke:#d29922;stroke-width:1}
    .port.in.fixed{stroke:#0d1117;stroke-width:0.5}
    .const-label{font-size:9px;fill:#8b949e;font-weight:600}
    .const-stub,.port-fixed,.port-group .pin-desc{pointer-events:none}
    .wire-handle{fill:#484f58;stroke:#e6edf3;stroke-width:1;cursor:move;opacity:0.85}
    """

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" data-gate-graph="1">',
        f"<style>{style}</style>",
        *header_elems,
        '<g id="wires">',
        *wire_elems,
        "</g>",
        '<g id="io">',
        *io_elems,
        "</g>",
        '<g id="gates">',
        *gate_elems,
        "</g>",
        '<g id="wire-handles"></g>',
        "</svg>",
    ]
    return "\n".join(lines)


def export_gate_graph_html(nl: Netlist) -> str:
    from pathlib import Path

    svg = export_gate_graph_svg(nl)
    js_path = Path(__file__).resolve().parents[1] / "hw" / "viewer" / "gate-graph-interactive.js"
    interactive_js = js_path.read_text(encoding="utf-8")
    title = "ALU8 gate connectivity"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(title)}</title>
  <style>
    html, body {{ margin: 0; height: 100%; background: #0d1117; overflow: hidden;
      -webkit-user-select: none; user-select: none; }}
    #wrap {{ width: 100%; height: 100%; overflow: auto; cursor: grab;
      -webkit-user-select: none; user-select: none; }}
    #stage, #stage svg {{ -webkit-user-select: none; user-select: none; }}
    #wrap:active {{ cursor: grabbing; }}
    #toolbar {{
      position: fixed; top: 8px; right: 8px; z-index: 10;
      background: #161b22; border: 1px solid #30363d; border-radius: 6px;
      padding: 6px 10px; font: 12px system-ui; color: #e6edf3;
    }}
    #toolbar button {{
      margin-left: 4px; padding: 4px 8px; cursor: pointer;
      background: #21262d; color: #e6edf3; border: 1px solid #484f58; border-radius: 4px;
    }}
    #stage {{ transform-origin: 0 0; }}
  </style>
</head>
<body>
  <div id="toolbar">
  <div>Drag gates · drag wires/IO · hover/click net to highlight · pan empty area</div>
  <div id="sel-status" style="margin:4px 0 6px;font-size:11px;color:#8b949e">(ready)</div>
  <div>
    Zoom: <button type="button" id="zin">+</button>
    <button type="button" id="zout">-</button>
    <button type="button" id="zreset">100%</button>
  </div>
  </div>
  <div id="wrap">
    <div id="stage">{svg}</div>
  </div>
  <script>
    const stage = document.getElementById('stage');
    const wrap = document.getElementById('wrap');
    let scale = 1;
    function applyScale() {{
      stage.style.transform = 'scale(' + scale + ')';
    }}
    document.getElementById('zin').onclick = () => {{ scale *= 1.15; applyScale(); }};
    document.getElementById('zout').onclick = () => {{ scale /= 1.15; applyScale(); }};
    document.getElementById('zreset').onclick = () => {{ scale = 1; applyScale(); }};
    wrap.addEventListener('wheel', (e) => {{
      e.preventDefault();
      scale *= e.deltaY < 0 ? 1.08 : 1/1.08;
      applyScale();
    }}, {{ passive: false }});
  </script>
  <script>
{interactive_js}
    initGateGraphInteractive(document.getElementById('stage'));
  </script>
</body>
</html>
"""
