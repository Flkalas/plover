"""CPLD control research netlist generation tests."""

from pathlib import Path

from hwsim.netlist import load_netlist, validate_netlist
from hwsim.units.catalog import load_catalog, validate_catalog


def test_counter_netlist_validates():
    root = Path(__file__).resolve().parents[1]
    nl_path = root / "hw/netlist/research/cpld_ctrl_counter.yaml"
    cat_path = root / "hw/units/research/cpld_ctrl_counter.yaml"
    nl = load_netlist(nl_path)
    units = load_catalog(cat_path)
    assert nl.block == "cpld_ctrl_counter"
    assert len(units) >= 25
    assert not validate_netlist(nl, root)
    assert not validate_catalog(nl, units)
    text = nl_path.read_text(encoding="utf-8")
    assert "net_mem_rd" in text


def test_cw16_netlist_has_two_latches():
    root = Path(__file__).resolve().parents[1]
    nl_path = root / "hw/netlist/research/cpld_ctrl_cw16.yaml"
    cat_path = root / "hw/units/research/cpld_ctrl_cw16.yaml"
    nl = load_netlist(nl_path)
    units = load_catalog(cat_path)
    assert nl.block == "cpld_ctrl_cw16"
    refs = {u.package_ref for u in units if u.kind == "latch8"}
    assert refs == {"U_LATCH_STB", "U_LATCH_ALU"}
    assert len(units) >= 5
    assert not validate_catalog(nl, units)
