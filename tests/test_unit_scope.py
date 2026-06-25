"""Unit scope tests."""

from pathlib import Path

from hwsim.netlist import load_netlist
from hwsim.units.catalog import load_alu8_catalog
from hwsim.units.scope import unit_scope


def _unit(unit_id: str):
    return next(u for u in load_alu8_catalog() if u.id == unit_id)


def test_not_gate_scope_pins_not_whole_chip():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    scope = unit_scope(nl, _unit("not_0"))
    assert "net_b0" in scope.nets
    assert "net_b_inv0" in scope.nets
    assert len(scope.gate_pins) == 2
    pkgs = {p.pkg for p in scope.gate_pins}
    assert any("04" in p for p in pkgs)


def test_mux4_b_only_one_mux_pins():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    scope = unit_scope(nl, _unit("mux4_b_0_1"))
    logicals = {p.logical for p in scope.gate_pins if p.pkg == "U_ALU_153_B_0"}
    assert "1Y" in logicals
    assert "2Y" not in logicals
    assert "2C0" not in logicals


def test_adder_lo_gate_pins_and_carry_net():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    scope = unit_scope(nl, _unit("283_lo"))
    assert "net_c_lo" in scope.nets
    assert any(p.pkg == "U_ALU_283_LO" for p in scope.gate_pins)
    assert not any(p.pkg == "U_ALU_283_HI" for p in scope.gate_pins)
