"""Unit catalog tests."""

from pathlib import Path

from hwsim.netlist import load_netlist
from hwsim.units.catalog import UNIT_KINDS, load_alu8_catalog, validate_catalog


def test_alu8_catalog_has_34_units():
    units = load_alu8_catalog()
    assert len(units) == 34
    kinds = {u.kind for u in units}
    assert kinds == UNIT_KINDS


def test_catalog_validates_against_netlist():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = load_alu8_catalog(root / "hw/units/alu8.yaml")
    assert validate_catalog(nl, units) == []


def test_stage_counts():
    units = load_alu8_catalog()
    stages = {}
    for u in units:
        stages[u.stage] = stages.get(u.stage, 0) + 1
    assert stages[1] == 2
    assert stages[2] == 16
    assert stages[3] == 8
    assert stages[4] == 8
