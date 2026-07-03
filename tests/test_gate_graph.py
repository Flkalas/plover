"""Gate connectivity graph tests."""

from pathlib import Path

from hwsim.export_gate_graph import export_gate_graph_svg
from hwsim.netlist import load_netlist
from hwsim.units.catalog import load_alu8_catalog
from hwsim.units.gate_graph import build_gate_graph, is_external_net


def test_gate_graph_has_all_units():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = load_alu8_catalog()
    graph = build_gate_graph(nl, units)
    assert len(graph.units) == 18
    assert len(graph.ports) > 80


def test_gate_graph_svg():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    svg = export_gate_graph_svg(nl)
    assert 'data-gate-graph="1"' in svg
    assert svg.count('class="gate-node"') == 18
    assert 'class="chip"' not in svg
    assert 'class="wire-hit"' in svg
    assert 'class="net"' in svg
    assert 'wire-trunk"' in svg
    assert 'net-junction"' in svg
    assert 'data-port-side="bottom"' in svg
    assert 'class="port in bottom"' in svg
    assert 'class="pin-desc"' in svg
    assert 'data-pin-desc="A"' in svg
    assert 'data-pin-desc="D0"' in svg
    assert 'data-pin-desc="Y"' in svg


def test_b_operand_io_labels_and_internal_inv():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    svg = export_gate_graph_svg(nl)

    for i in range(8):
        assert f'class="io-label">a{i}</text>' in svg
    assert 'class="io-label">B</text>' not in svg
    assert 'class="io-bus"' not in svg
    assert 'class="io-net" data-net="net_b153_sel0"' not in svg
    assert 'wire-seg" data-net="net_b_add0"' in svg

    assert is_external_net("net_a0")
    assert not is_external_net("net_b153_sel0")
    assert not is_external_net("net_b_add0")

    assert 'class="net" data-net="net_a0"' in svg
    assert 'data-topology="column_vertical"' in svg
    assert 'data-route-x="' in svg
    assert svg.count('data-route-x="') >= 60


def test_mux_bit_matches_153_data_select_layout():
    """Bit-slice MUX: logic C* left, shared A/B select bottom."""
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    svg = export_gate_graph_svg(nl)
    import re

    c0 = re.search(r'<circle[^>]*data-unit="mux4_bit_0"[^>]*data-logical="1C0"[^>]*/>', svg)
    a_sel = re.search(r'<circle[^>]*data-unit="mux4_bit_0"[^>]*data-logical="A"[^>]*/>', svg)
    assert c0 and 'data-port-side="left"' in c0.group()
    assert a_sel and 'data-port-side="bottom"' in a_sel.group()
    assert 'data-unit="mux4_bit_0" data-logical="1G" data-value="0"' in svg
    assert 'data-unit="mux4_bit_0" data-logical="2G" data-value="0"' in svg
    assert svg.count('data-unit="mux4_bit_0" data-logical="1C') == 4
    b_sel = re.search(r'<circle[^>]*data-unit="mux4_bit_0"[^>]*data-logical="B"[^>]*/>', svg)
    assert b_sel and 'data-port-side="bottom"' in b_sel.group()


def test_mux_bit_shows_bctrl_inputs():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    svg = export_gate_graph_svg(nl)
    assert 'data-unit="mux4_bit_0" data-logical="2C0"' in svg
    assert 'data-unit="mux4_bit_0" data-logical="2C3"' in svg
    assert 'data-unit="mux4_bit_0" data-logical="2G" data-value="0"' in svg
    assert 'data-unit="mux2_y_0" data-logical="OE" data-value="0"' in svg


def test_bottom_ports_have_distinct_stub_y():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    svg = export_gate_graph_svg(nl)
    import re

    bottom_wired = re.findall(
        r'class="port in bottom"[^>]*data-unit="mux4_bit_0"[^>]*data-stub-y="([\d.]+)"',
        svg,
    )
    assert len(bottom_wired) == 2
    assert float(bottom_wired[0]) != float(bottom_wired[1])
    assert float(bottom_wired[0]) < float(bottom_wired[1])
