"""Branching wire layout tests."""

from hwsim.wiring.gate_branch import BRANCH_LEAD, layout_branch_net


def test_operand_bus_has_trunk_and_spokes():
    io = (60.0, 100.0, "io", "io", 60.0, 100.0)
    gates = [
        (180.0, 112.0, "not_0", "left", 170.0, 112.0),
        (320.0, 82.0, "153_0_1", "left", 310.0, 82.0),
        (620.0, 126.0, "153_0_2", "left", 602.0, 126.0),
    ]
    branch = layout_branch_net([io, *gates], "net_b0")
    assert branch.topology == "bus_horizontal"
    assert branch.hub is None
    assert len(branch.junctions) == 3
    roles = {s.role for s in branch.segments}
    assert roles == {"trunk", "spoke"}
    assert sum(1 for s in branch.segments if s.role == "trunk") == 1
    assert sum(1 for s in branch.segments if s.role == "spoke") == 3


def test_operand_bus_mixed_left_and_bottom():
    """Operand net with left ports + bottom select (MUX L A/B after pin layout fix)."""
    io = (80.0, 128.0, "io", "io", 80.0, 128.0)
    gates = [
        (220.0, 124.0, "not_0", "left", 206.0, 124.0),
        (400.0, 86.0, "mux4_b_0_1", "left", 386.0, 86.0),
        (768.0, 176.0, "mux4_l_0", "bottom", 779.0, 196.0),
    ]
    branch = layout_branch_net([io, *gates], "net_b0")
    assert branch.topology == "bus_mixed"
    bottom_spoke = next(s for s in branch.segments if s.endpoint == "mux4_l_0")
    ys = [p[1] for p in bottom_spoke.points]
    assert max(ys) <= 196.0 + 0.01
    assert min(ys) >= 128.0 - 0.01
    assert not any(abs(y - 128.0) < 0.01 and abs(x - 789.0) < 0.01 for x, y in bottom_spoke.points[1:])


def test_control_net_corridor():
    io = (328.0, 1096.0, "io", "io", 328.0, 1096.0)
    gates = [
        (320.0, 152.0, "153_0_1", "bottom", 338.0, 168.0),
        (320.0, 272.0, "153_1_1", "bottom", 346.0, 288.0),
    ]
    branch = layout_branch_net([io, *gates], "net_b_sel")
    assert branch.topology == "corridor_vertical"
    trunk = next(s for s in branch.segments if s.role == "trunk")
    assert trunk.points[0] == (328.0, 1096.0)
    assert trunk.points[-1][1] == 168.0
    stub_ys = {p[1] for seg in branch.segments if seg.role == "spoke" for p in seg.points[:2]}
    assert len(stub_ys) >= 2


def test_control_lgc_column_with_io():
    """Control decode at bottom IO ??channel trunk + row spokes (no U-turn)."""
    io = (760.0, 1352.0, "io", "io", 760.0, 1352.0)
    gates = [
        (760.0, 86.0, "mux4_l_0", "left", 746.0, 86.0),
        (760.0, 238.0, "mux4_l_1", "left", 736.0, 238.0),
        (760.0, 390.0, "mux4_l_2", "left", 726.0, 390.0),
        (760.0, 542.0, "mux4_l_3", "left", 716.0, 542.0),
    ]
    branch = layout_branch_net([io, *gates], "net_lgc0")
    assert branch.topology == "column_vertical"
    trunk_x = 716.0 - BRANCH_LEAD
    feeder = next(s for s in branch.segments if s.role == "trunk" and s.endpoint == "io")
    assert feeder.points[0] == (760.0, 1352.0)
    assert feeder.points[-1] == (trunk_x, 1352.0)
    vertical = next(s for s in branch.segments if s.role == "trunk" and s.endpoint == "")
    assert vertical.points[0] == (trunk_x, 86.0)
    assert vertical.points[-1] == (trunk_x, 1352.0)
    spoke = next(s for s in branch.segments if s.endpoint == "mux4_l_0")
    assert spoke.points[0] == (trunk_x, 86.0)
    assert spoke.points[-1] == (760.0, 86.0)
    assert len(spoke.points) == 3


def test_control_lgc_column_io_above():
    """IO above column fans down through the same channel trunk."""
    io = (760.0, 40.0, "io", "io", 760.0, 40.0)
    gates = [
        (760.0, 86.0, "mux4_l_0", "left", 746.0, 86.0),
        (760.0, 238.0, "mux4_l_1", "left", 736.0, 238.0),
        (760.0, 390.0, "mux4_l_2", "left", 726.0, 390.0),
    ]
    branch = layout_branch_net([io, *gates], "net_lgc0")
    trunk_x = 726.0 - BRANCH_LEAD
    vertical = next(s for s in branch.segments if s.role == "trunk" and s.endpoint == "")
    assert vertical.points[0] == (trunk_x, 40.0)
    assert vertical.points[-1] == (trunk_x, 390.0)


def test_internal_lgc_column_vertical():
    """net_lgc* fans out to MUX L stack: vertical trunk, not star hub."""
    gates = [
        (760.0, 86.0, "mux4_l_0", "left", 746.0, 86.0),
        (760.0, 238.0, "mux4_l_1", "left", 736.0, 238.0),
        (760.0, 390.0, "mux4_l_2", "left", 726.0, 390.0),
        (760.0, 542.0, "mux4_l_3", "left", 716.0, 542.0),
    ]
    branch = layout_branch_net(gates, "net_lgc0")
    assert branch.topology == "column_vertical"
    assert branch.hub is None
    trunk_x = 716.0 - BRANCH_LEAD
    trunk = next(s for s in branch.segments if s.role == "trunk")
    assert trunk.points[0][0] == trunk_x
    assert trunk.points[0][1] == 86.0
    assert trunk.points[1][1] == 542.0


def test_same_gate_bottom_ports_different_stub_y():
    py = 152.0
    anchors = [
        (328.0, py, "mux4_b_0_1", "bottom", 338.0, py + 16.0),
        (356.0, py, "mux4_b_0_1", "bottom", 346.0, py + 24.0),
    ]
    assert anchors[0][5] != anchors[1][5]


def test_inv_link_is_single_segment():
    gates = [
        (224.0, 112.0, "not_0", "right", 234.0, 112.0),
        (320.0, 126.0, "153_0_1", "left", 302.0, 126.0),
    ]
    branch = layout_branch_net(gates, "net_b_inv0")
    assert branch.topology == "link"
    assert len(branch.segments) == 1
    assert branch.segments[0].role == "link"
