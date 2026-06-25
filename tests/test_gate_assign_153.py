"""153 slice global mux assignment."""

from pathlib import Path

from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS
from hwsim.netlist import load_netlist
from hwsim.placement.gate_assign import optimize_all_gate_assign
from hwsim.placement.graph import build_gate_units
from hwsim.placement.pack import build_part_families, default_packages, merge_packages_with_assign
from hwsim.placement.anchors import compute_default_positions
from hwsim.export_schematic import ASSEMBLY_LAYOUT
from hwsim.pinout import load_pinout


def test_153_slice_assign_eight_slices():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    slice_units = [u for u in units if u.part == "ALU_153_SLICE"]
    assert len(slice_units) == 8

    base_pkgs = default_packages(nl, assembly=True)
    pinouts = {p.part: load_pinout(p.part) for p in base_pkgs}
    families = build_part_families(nl, units, base_pkgs, assembly=True)
    positions = compute_default_positions(base_pkgs, ASSEMBLY_LAYOUT, cols=3, assembly=True)

    assign = optimize_all_gate_assign(
        {"ALU_153_SLICE": families["ALU_153_SLICE"]},
        slice_units,
        positions,
        pinouts,
        seed=1,
    )
    merged = merge_packages_with_assign(nl, assign, slice_units, assembly=True)
    l_pkgs = [p for p in merged if p.part == "74HC153" and "_L_" in p.id]
    assert len(l_pkgs) == 4
    refs = []
    for p in l_pkgs:
        refs.extend(p.instance_refs)
    assert len(refs) == 8
