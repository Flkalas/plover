"""Schematic layout and SVG export tests."""

from __future__ import annotations

from simulators.cyclesim.export.alu8_netlist import build_alu8_func_netlist, port_net_names
from simulators.cyclesim.export.schematic.alu8_template import (
    A_ROW_OFFSET,
    B_ROW_OFFSET,
    ROW_PITCH,
    Y_ROW_OFFSET,
    build_alu8_template,
)
from simulators.cyclesim.export.schematic.router import build_route_assignments, chip_anchors
from simulators.cyclesim.export.schematic_layout import (
    collect_all_routes,
    layout_alu8_schematic,
    net_anchor_map,
    render_alu8_schematic_svg,
    wires_avoid_chips,
)


def test_twelve_symbol_instances() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    assert len(layout.instances) == 12


def test_net_b_add0_shared_anchors() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)["net_b_add0"]
    refs = {(a.ref, a.pin) for a in anchors if a.ref and a.ref != "__port__"}
    assert ("U_ALU_153_0", "2Y") in refs
    assert ("U_ALU_283_LO", "B0") in refs


def test_net_c_lo_add_chain() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)["net_c_lo"]
    refs = {(a.ref, a.pin) for a in anchors if a.ref and a.ref != "__port__"}
    assert ("U_ALU_283_LO", "COUT") in refs
    assert ("U_ALU_283_HI", "CIN") in refs


def test_svg_contains_symbols_and_nets() -> None:
    netlist = build_alu8_func_netlist()
    svg, w, h = render_alu8_schematic_svg(netlist, port_names=port_net_names())
    assert w > 400 and h > 400
    assert "<svg" in svg
    assert 'class="symbol"' in svg
    assert 'data-ref="U_ALU_153_0"' in svg
    assert 'data-ref="U_ALU_157_YBP_0"' in svg
    assert "U_CMP_SUB" not in svg
    assert 'class="net"' in svg
    assert 'data-net="net_a0"' in svg


def test_bus_net_distinct_stroke_colors() -> None:
    netlist = build_alu8_func_netlist()
    svg, _, _ = render_alu8_schematic_svg(netlist, port_names=port_net_names())
    assert 'data-net="net_cin"' in svg
    assert 'data-net="net_lgc0"' in svg
    assert 'data-net="net_bctrl0"' in svg
    assert "#58a6ff" in svg
    assert "#a371f7" in svg
    assert "#e3b341" in svg
    assert 'class="grid"' in svg
    assert 'class="bus-rail"' in svg
    assert "net-junction" in svg


def test_symbols_align_to_grid() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    for inst in layout.instances:
        assert inst["x"] % 10 == 0
        assert inst["y"] % 10 == 0
        assert inst["w"] % 10 == 0
        assert inst["h"] % 10 == 0
    for anchor in layout.anchors:
        if anchor.ref == "__port__":
            continue
        assert anchor.x % 10 == 0
        assert anchor.y % 10 == 0


def test_internal_channel_trunks_not_shared() -> None:
    """Each internal datapath net gets its own channel trunk grid line."""
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    tmpl = build_alu8_template()
    by_net: dict[str, list] = {}
    for anchor in layout.anchors:
        by_net.setdefault(anchor.net, []).append(anchor)
    plans, _, _, _ = build_route_assignments(by_net, tmpl, port_net_names())
    internal_prefixes = ("net_b_add", "net_sum", "net_y_logic")
    trunks = [
        plan.trunk_y
        for net, plan in plans.items()
        if net == "net_c_lo" or net.startswith(internal_prefixes)
    ]
    assert len(trunks) == len(set(trunks))


def test_port_rows_align_with_153_ab() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)
    for i in range(8):
        port_a = next(a for a in anchors[f"net_a{i}"] if a.ref == "__port__")
        chip_a = next(
            a for a in anchors[f"net_a{i}"] if a.ref == f"U_ALU_153_{i}" and a.pin == "A"
        )
        port_b = next(a for a in anchors[f"net_b{i}"] if a.ref == "__port__")
        chip_b = next(
            a for a in anchors[f"net_b{i}"] if a.ref == f"U_ALU_153_{i}" and a.pin == "B"
        )
        assert port_a.y == chip_a.y
        assert port_b.y == chip_b.y


def test_y_ports_align_with_157() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)
    for i in range(8):
        ref = "U_ALU_157_YBP_0" if i < 4 else "U_ALU_157_YBP_1"
        pin = f"{i % 4 + 1}Y"
        port_y = next(a for a in anchors[f"net_y{i}"] if a.ref == "__port__")
        chip_y = next(a for a in anchors[f"net_y{i}"] if a.ref == ref and a.pin == pin)
        assert port_y.y == chip_y.y


def test_lgc_bctrl_horizontal_only() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    routes = collect_all_routes(layout, port_net_names())
    max_span = ROW_PITCH * 3
    for net in [f"net_lgc{i}" for i in range(4)] + [f"net_bctrl{i}" for i in range(4)]:
        for path in routes[net]:
            for i in range(len(path) - 1):
                x0, y0 = path[i]
                x1, y1 = path[i + 1]
                if x0 == x1 and abs(y1 - y0) > max_span:
                    raise AssertionError(f"{net} has tall vertical segment at x={x0}")


def test_wires_avoid_chip_bodies() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    assert wires_avoid_chips(layout, port_net_names())
