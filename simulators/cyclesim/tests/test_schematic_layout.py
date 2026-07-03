"""Schematic layout and SVG export tests."""

from __future__ import annotations

from simulators.cyclesim.export.alu8_netlist import build_alu8_func_netlist, port_net_names
from simulators.cyclesim.export.schematic_layout import (
    layout_alu8_schematic,
    net_anchor_map,
    render_alu8_schematic_svg,
)


def test_twenty_symbol_instances() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    assert len(layout.instances) == 20


def test_net_b_add0_shared_anchors() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)["net_b_add0"]
    refs = {(a.ref, a.pin) for a in anchors if a.ref and a.ref != "__port__"}
    assert ("U_MUX4_0", "Y_BADD") in refs
    assert ("U_ADD_LO", "B0") in refs


def test_net_c_lo_add_chain() -> None:
    netlist = build_alu8_func_netlist()
    layout = layout_alu8_schematic(netlist, port_names=port_net_names())
    anchors = net_anchor_map(layout)["net_c_lo"]
    refs = {(a.ref, a.pin) for a in anchors if a.ref and a.ref != "__port__"}
    assert ("U_ADD_LO", "COUT") in refs
    assert ("U_ADD_HI", "CIN") in refs


def test_svg_contains_symbols_and_nets() -> None:
    netlist = build_alu8_func_netlist()
    svg, w, h = render_alu8_schematic_svg(netlist, port_names=port_net_names())
    assert w > 400 and h > 400
    assert "<svg" in svg
    assert 'class="symbol"' in svg
    assert 'data-ref="U_MUX4_0"' in svg
    assert 'class="net"' in svg
    assert 'data-net="net_a0"' in svg


def test_control_net_orange_stroke() -> None:
    netlist = build_alu8_func_netlist()
    svg, _, _ = render_alu8_schematic_svg(netlist, port_names=port_net_names())
    assert 'data-net="net_cin"' in svg
    assert "#d29922" in svg
