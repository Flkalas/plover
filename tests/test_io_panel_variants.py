"""I/O panel left/right variants."""

from pathlib import Path

from hwsim.netlist import load_netlist
from hwsim.placement.run import optimize_layout


def test_io_left_and_right_variants():
    root = Path(__file__).resolve().parents[1]
    path = root / "hw/netlist/blocks/alu8.yaml"
    doc = optimize_layout(path, assembly=True, io_sides=("left", "right"), seed=0, sa_iterations=40)
    assert "io-left" in doc.variants
    assert "io-right" in doc.variants
    assert doc.variants["io-left"].io_panel.side == "left"
    assert doc.variants["io-right"].io_panel.side == "right"


def test_io_right_panel_pins_face_left():
    root = Path(__file__).resolve().parents[1]
    from hwsim.export_schematic import ASSEMBLY_LAYOUT, _route_from_panel, group_into_packages
    from hwsim.placement.anchors import build_anchors, compute_default_positions
    from hwsim.placement.io_panel import IO_PANEL_EDGE_MARGIN, build_io_panel_schematic

    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    doc = optimize_layout(root / "hw/netlist/blocks/alu8.yaml", io_sides=("right",), seed=0, sa_iterations=40)
    var = doc.variants["io-right"]
    panel = var.io_panel
    packages = group_into_packages(nl.instances, assembly=True)
    pos = compute_default_positions(packages, ASSEMBLY_LAYOUT, assembly=True)
    anchors, _ = build_anchors(packages, pos, layout=ASSEMBLY_LAYOUT, io_panel=panel, nl=nl)
    panel_anchors = [a for a in anchors if a.net.startswith("net_a0") or a.net == "net_a0"]
    assert panel_anchors
    assert panel_anchors[0].side == "left"

    canvas_w = 1200.0
    panel_by_net, panel_lane_x, _, _ = build_io_panel_schematic(
        panel,
        nl,
        margin=180.0,
        panel_width=128.0,
        lane_inset=12.0,
        lane_step=5.25,
        canvas_width=canvas_w,
    )
    hub = panel_by_net["net_a0"]
    assert hub.x > canvas_w - 128 - IO_PANEL_EDGE_MARGIN - 20
    assert panel_lane_x["net_a0"] < hub.x
    route = _route_from_panel(hub.x, hub.y, 500.0, hub.y, stub=22.0, lane_x=panel_lane_x["net_a0"], pin_side="left")
    first_seg_end = route.split()[1].split(",")[0]
    assert float(first_seg_end) < hub.x


def test_both_variants_have_metrics():
    root = Path(__file__).resolve().parents[1]
    doc = optimize_layout(root / "hw/netlist/blocks/alu8.yaml", io_sides=("left", "right"), seed=0, sa_iterations=40)
    for var in doc.variants.values():
        assert "total_wire_mm" in var.metrics
        assert "crossings" in var.metrics
