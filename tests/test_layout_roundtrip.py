"""layout.yaml roundtrip and schematic export."""

from pathlib import Path

from hwsim.export_schematic import export_schematic_svg
from hwsim.netlist import load_netlist
from hwsim.placement.layout_spec import layout_from_yaml, layout_to_yaml
from hwsim.placement.run import optimize_layout


def test_layout_yaml_roundtrip():
    root = Path(__file__).resolve().parents[1]
    doc = optimize_layout(root / "hw/netlist/blocks/alu8.yaml", io_sides=("left",), seed=0, sa_iterations=40)
    text = layout_to_yaml(doc)
    doc2 = layout_from_yaml(text)
    assert doc2.block == doc.block
    assert "io-left" in doc2.variants


def test_schematic_export_with_layout_spec():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    doc = optimize_layout(root / "hw/netlist/blocks/alu8.yaml", io_sides=("left",), seed=0, sa_iterations=40)
    var = doc.variants["io-left"]
    svg = export_schematic_svg(nl, assembly=True, layout_spec=var)
    assert "<svg" in svg
    assert "U_ALU_283" in svg or "chip" in svg
