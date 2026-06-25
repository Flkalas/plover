"""Gate-level schematic export tests."""

from pathlib import Path

from hwsim.export_gate_schematic import export_gate_schematic_svg
from hwsim.netlist import load_netlist
from hwsim.units.catalog import load_alu8_catalog


def test_not_gate_symbol():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    unit = next(u for u in load_alu8_catalog() if u.id == "not_0")
    svg = export_gate_schematic_svg(nl, unit)
    assert 'data-gate-view="1"' in svg
    assert 'id="gate"' in svg
    assert "net_b0" in svg
    assert "net_b_inv0" in svg
    assert 'class="chip"' not in svg


def test_mux4_gate_symbol():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    unit = next(u for u in load_alu8_catalog() if u.id == "mux4_b_0_1")
    svg = export_gate_schematic_svg(nl, unit)
    assert "4:1" in svg
    assert "net_b_add0" in svg


def test_adder_gate_symbol():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    unit = next(u for u in load_alu8_catalog() if u.id == "283_lo")
    svg = export_gate_schematic_svg(nl, unit)
    assert "4-bit" in svg
    assert "net_sum0" in svg
