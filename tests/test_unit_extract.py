"""Unit extract tests."""

from pathlib import Path

from hwsim.netlist import load_netlist
from hwsim.units.catalog import load_alu8_catalog
from hwsim.units.extract import extract_unit


def _unit(unit_id: str):
    units = {u.id: u for u in load_alu8_catalog()}
    return units[unit_id]


def test_mux4_b_slice_pins():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("mux4_b_0_1"))
    nets = {p.net for p in ex.boundary_ports}
    assert "net_b_add0" in nets
    assert "net_b0" in nets
    assert "net_b_inv0" in nets
    assert "net_b_sel" in nets
    fixed = {fp.logical_pin: fp.value for fp in ex.fixed_ports}
    assert fixed == {"C2": "1", "C3": "1", "G": "0"}


def test_mux4_b_bit1_inc_lsb_zero():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("mux4_b_0_2"))
    fixed = {fp.logical_pin: fp.value for fp in ex.fixed_ports}
    assert fixed == {"C2": "0", "C3": "1", "G": "0"}


def test_mux4_l_enable_tied_low():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("mux4_l_0"))
    fixed = {fp.logical_pin: fp.value for fp in ex.fixed_ports}
    assert fixed == {"G": "0"}


def test_mux2_y_output_enable_tied_low():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("mux2_y_3"))
    fixed = {fp.logical_pin: fp.value for fp in ex.fixed_ports}
    assert fixed == {"OE": "0"}


def test_mux2_y_bit3():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("mux2_y_3"))
    nets = {p.net for p in ex.boundary_ports}
    assert "net_sum3" in nets
    assert "net_y_logic3" in nets
    assert "net_y3" in nets
    assert "net_y_mux_sel" in nets
    out = [p for p in ex.boundary_ports if p.direction == "out"]
    assert any(p.net == "net_y3" for p in out)


def test_adder4_carry_ports():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    ex = extract_unit(nl, _unit("283_lo"))
    nets = {p.net for p in ex.boundary_ports}
    assert "net_c_lo" in nets
    assert "net_cin" in nets
    assert "net_sum0" in nets
