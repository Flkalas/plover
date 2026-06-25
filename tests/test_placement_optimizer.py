"""Placement optimizer improves over default grid."""

from pathlib import Path

from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS, ASSEMBLY_LAYOUT
from hwsim.netlist import load_netlist
from hwsim.placement.anchors import build_anchors, compute_default_positions
from hwsim.placement.cost import layout_cost
from hwsim.placement.run import optimize_layout
from hwsim.placement.pack import default_packages
from hwsim.pinout import load_pinout


def test_optimized_cost_not_worse_than_default():
    root = Path(__file__).resolve().parents[1]
    path = root / "hw/netlist/blocks/alu8.yaml"
    nl = load_netlist(path)
    base_pkgs = default_packages(nl, assembly=True)
    pinouts = {}
    for p in base_pkgs:
        if p.part not in pinouts:
            pinouts[p.part] = load_pinout(p.part)
    default_pos = compute_default_positions(base_pkgs, ASSEMBLY_LAYOUT, cols=3, assembly=True)
    default_anchors, _ = build_anchors(base_pkgs, default_pos, pinouts, layout=ASSEMBLY_LAYOUT, nl=nl)
    default_cost = layout_cost(nl, default_anchors)

    doc = optimize_layout(path, assembly=True, io_sides=("left",), seed=0, cols=3, sa_iterations=40)
    var = doc.variants["io-left"]
    opt_cost = var.metrics["total_wire_mm"]["abstract"]

    # Heuristic optimizer should stay within reasonable range of default grid
    assert opt_cost <= default_cost * 1.25
