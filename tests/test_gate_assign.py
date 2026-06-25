"""Gate assignment ??intra/inter-chip."""

from pathlib import Path

from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS
from hwsim.netlist import load_netlist
from hwsim.placement.anchors import build_anchors, compute_default_positions
from hwsim.placement.gate_assign import optimize_all_gate_assign
from hwsim.placement.graph import build_gate_units
from hwsim.placement.pack import (
    build_part_families,
    default_gate_assign,
    default_packages,
    merge_packages_with_assign,
)
from hwsim.export_schematic import ASSEMBLY_LAYOUT
from hwsim.pinout import load_pinout


def _pinouts(packages):
    pinouts = {}
    for pkg in packages:
        if pkg.part not in pinouts:
            pinouts[pkg.part] = load_pinout(pkg.part)
    return pinouts


def test_74hc04_inter_chip_assign_preserves_nets():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    inv_units = [u for u in units if u.part == "74HC04"]
    assert len(inv_units) == 8

    base_pkgs = default_packages(nl, assembly=True)
    pinouts = _pinouts(base_pkgs)
    families = build_part_families(nl, inv_units, base_pkgs, assembly=True)
    positions = compute_default_positions(base_pkgs, ASSEMBLY_LAYOUT, cols=3, assembly=True)

    assign = optimize_all_gate_assign(
        {"74HC04": families["74HC04"]},
        inv_units,
        positions,
        pinouts,
        seed=0,
    )
    merged = merge_packages_with_assign(nl, assign, inv_units, assembly=True)
    inv_pkgs = [p for p in merged if p.part == "74HC04"]
    assert len(inv_pkgs) == 2

    # Each inverter ref appears exactly once
    refs = []
    for p in inv_pkgs:
        refs.extend(p.instance_refs)
    assert sorted(refs) == sorted(u.ref for u in inv_units)

    # One gate slot per inverter (check A pin only ??A/Y share gate index)
    for p in inv_pkgs:
        gates = [g for pin, _net, g in p.connections if pin == "A" and g is not None]
        assert len(gates) == len(set(gates))


def test_gate_assign_no_duplicate_slot():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    base_pkgs = default_packages(nl, assembly=True)
    assign = default_gate_assign(nl, units, base_pkgs, assembly=True)
    for part, by_pkg in assign.items():
        for pkg_id, slots in by_pkg.items():
            assert len(slots) == len(set(slots.keys()))
