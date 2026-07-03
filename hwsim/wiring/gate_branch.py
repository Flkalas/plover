"""Branching wire layout: trunk + spokes, corridor, hub star, or direct link."""

from __future__ import annotations

from dataclasses import dataclass

from hwsim.export_schematic import _is_control_net
from hwsim.units.gate_graph import is_a_operand_bit_net, is_b_operand_bit_net

BOTTOM_STUB = 16.0
BOTTOM_STUB_STEP = 8.0
BRANCH_LEAD = 14.0
COLUMN_X_TOL = 36.0
COLUMN_Y_SPAN = 80.0

# (port_x, port_y, unit_id, side, route_x, stub_y)
# stub_y: horizontal bend Y for bottom ports; equals port_y for other sides
Anchor = tuple[float, float, str, str, float, float]


@dataclass
class WireSeg:
    role: str  # trunk | spoke | link
    endpoint: str  # unit_id, "io", or ""
    points: list[tuple[float, float]]


@dataclass
class BranchNet:
    topology: str  # bus_horizontal | bus_mixed | corridor_vertical | column_vertical | link | star
    hub: tuple[float, float] | None
    junctions: list[tuple[float, float, str]]  # x, y, endpoint unit_id
    segments: list[WireSeg]


def _dedupe_xy(path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not path:
        return path
    out = [path[0]]
    for p in path[1:]:
        if abs(p[0] - out[-1][0]) > 0.01 or abs(p[1] - out[-1][1]) > 0.01:
            out.append(p)
    return out


def fmt_path(path: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in _dedupe_xy(path))


def _unpack(anchor: Anchor) -> tuple[float, float, str, str, float, float]:
    if len(anchor) >= 6:
        return anchor[0], anchor[1], anchor[2], anchor[3], anchor[4], anchor[5]
    px, py, uid, side, rx = anchor[:5]
    stub_y = py + BOTTOM_STUB if side == "bottom" else py
    return px, py, uid, side, rx, stub_y


def _split_io_gate(pts: list[Anchor]) -> tuple[list[Anchor], list[Anchor]]:
    ios = [p for p in pts if p[2] == "io"]
    gates = [p for p in pts if p[2] != "io"]
    return ios, gates


def _is_153_left_data_net(net: str) -> bool:
    return net.startswith("net_lgc") or net.startswith("net_bctrl")


def _partition_sides(gates: list[Anchor]) -> tuple[list[Anchor], list[Anchor], list[Anchor]]:
    left = [g for g in gates if g[3] == "left"]
    right = [g for g in gates if g[3] == "right"]
    bottom = [g for g in gates if g[3] == "bottom"]
    return left, right, bottom


def _is_column_fanout(left: list[Anchor]) -> bool:
    """Left ports stacked in one column (e.g. net_lgc* on MUX L)."""
    if len(left) < 3:
        return False
    xs = [g[0] for g in left]
    ys = [g[1] for g in left]
    return (max(xs) - min(xs) <= COLUMN_X_TOL) and (max(ys) - min(ys) >= COLUMN_Y_SPAN)


def _layout_inv_link(gates: list[Anchor]) -> list[tuple[float, float]]:
    if len(gates) < 2:
        return [(g[0], g[1]) for g in gates]
    src = next((g for g in gates if g[3] == "right"), gates[0])
    dst = next((g for g in gates if g[3] == "left"), gates[-1])
    sx, sy, _, _, srx, _ = _unpack(src)
    dx, dy, _, _, drx, _ = _unpack(dst)
    path: list[tuple[float, float]] = [(sx, sy), (srx, sy), (drx, sy)]
    if abs(sy - dy) > 0.5:
        path.append((drx, dy))
    path.append((dx, dy))
    return path


def _spoke_left_from_bus(px: float, py: float, rx: float, bus_y: float) -> list[tuple[float, float]]:
    """Horizontal bus tap ??vertical at route_x ??into left port."""
    return _dedupe_xy([(rx, bus_y), (rx, py), (px, py)])


def _spoke_left_from_column(px: float, py: float, rx: float, trunk_x: float) -> list[tuple[float, float]]:
    """Vertical trunk tap ??horizontal at row Y ??into left port."""
    return _dedupe_xy([(trunk_x, py), (rx, py), (px, py)])


def _spoke_bottom_from_trunk(
    px: float, py: float, rx: float, spine_x: float, stub_y: float
) -> list[tuple[float, float]]:
    """Vertical spine tap at stub Y ??horizontal via route_x ??into bottom port."""
    pts: list[tuple[float, float]] = [(spine_x, stub_y), (rx, stub_y), (rx, py)]
    if abs(px - rx) > 0.01:
        pts.append((px, py))
    return _dedupe_xy(pts)


def _spoke_left_to_hub(px: float, py: float, rx: float, hx: float, hy: float) -> list[tuple[float, float]]:
    return _dedupe_xy([(px, py), (rx, py), (rx, hy), (hx, hy)])


def _spoke_right_to_hub(px: float, py: float, rx: float, hx: float, hy: float) -> list[tuple[float, float]]:
    return _dedupe_xy([(px, py), (rx, py), (rx, hy), (hx, hy)])


def _spoke_bottom_to_hub(
    px: float, py: float, rx: float, hx: float, hy: float, stub_y: float
) -> list[tuple[float, float]]:
    return _dedupe_xy([(px, py), (px, stub_y), (rx, stub_y), (rx, hy), (hx, hy)])


def _route_to_hub(anchor: Anchor, hx: float, hy: float) -> list[tuple[float, float]]:
    px, py, _, side, rx, stub_y = _unpack(anchor)
    if side == "io":
        if abs(py - hy) < 0.01:
            return [(px, py), (hx, hy)]
        return [(px, py), (px, hy), (hx, hy)]
    if side == "left":
        return _spoke_left_to_hub(px, py, rx, hx, hy)
    if side == "right":
        return _spoke_right_to_hub(px, py, rx, hx, hy)
    return _spoke_bottom_to_hub(px, py, rx, hx, hy, stub_y)


def _layout_link(pts: list[Anchor], net: str) -> BranchNet:
    ios, gates = _split_io_gate(pts)
    io = ios[0] if ios else None
    if net.startswith("net_b_inv"):
        path = _layout_inv_link(gates)
        return BranchNet("link", None, [], [WireSeg("link", "", path)])
    if len(pts) == 2:
        a, b = pts
        if a[3] in ("left", "right") and b[3] in ("left", "right"):
            path = _layout_inv_link([a, b]) if a[3] == "right" else _layout_inv_link([b, a])
        else:
            path = _dedupe_xy([(a[0], a[1]), (b[0], b[1])])
        return BranchNet("link", None, [], [WireSeg("link", "", path)])
    ordered = ([io] if io else []) + sorted(gates, key=lambda p: (_unpack(p)[4], p[0]))
    path: list[tuple[float, float]] = []
    for i, anchor in enumerate(ordered):
        px, py, _, side, rx, stub_y = _unpack(anchor)
        if i == 0:
            path.append((px, py))
            if side in ("left", "right"):
                path.append((rx, py))
            continue
        prev_rx = _unpack(ordered[i - 1])[4]
        if side == "left":
            path.extend([(rx, path[-1][1]), (rx, py), (px, py)])
        elif side == "right":
            path.extend([(prev_rx, py), (rx, py), (px, py)])
        else:
            path.extend([(px, stub_y), (rx, stub_y), (rx, py)])
            if abs(px - rx) > 0.01:
                path.append((px, py))
    return BranchNet("link", None, [], [WireSeg("link", "", _dedupe_xy(path))])


def _corridor_row_y(left: list[Anchor], bottom: list[Anchor], fallback: float) -> float:
    """Row height for the horizontal bus span between 153 and 283."""
    left_ys = [_unpack(g)[1] for g in left]
    if left_ys:
        return min(left_ys)
    stub_ys = [_unpack(g)[5] for g in bottom]
    return min(stub_ys) if stub_ys else fallback


def _layout_operand_corridor_a(
    io: Anchor, left: list[Anchor], bottom: list[Anchor]
) -> BranchNet:
    """A bus: bottom IO ↑ to row Y, horizontal trunk across corridor, taps to 283 and 153."""
    io_x, io_y, _, _, _, _ = _unpack(io)
    row_y = _corridor_row_y(left, bottom, io_y)
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []

    tap_xs = [io_x, *(_unpack(a)[4] for a in left + bottom)]
    x_lo, x_hi = min(tap_xs), max(tap_xs)

    if io_y > row_y + 0.5:
        segments.append(WireSeg("trunk", "io", [(io_x, io_y), (io_x, row_y)]))
    segments.append(WireSeg("trunk", "", [(x_lo, row_y), (x_hi, row_y)]))

    for anchor in sorted(left, key=lambda p: _unpack(p)[1]):
        px, py, uid, _, rx, _ = _unpack(anchor)
        junctions.append((rx, row_y, uid))
        if abs(py - row_y) < 0.5:
            segments.append(WireSeg("spoke", uid, [(rx, row_y), (px, py)]))
        else:
            segments.append(WireSeg("spoke", uid, _dedupe_xy([(rx, row_y), (rx, py), (px, py)])))

    for anchor in sorted(bottom, key=lambda p: (_unpack(p)[5], _unpack(p)[4])):
        px, py, uid, _, rx, stub_y = _unpack(anchor)
        junctions.append((rx, row_y, uid))
        segments.append(
            WireSeg(
                "spoke",
                uid,
                _dedupe_xy([(rx, row_y), (rx, stub_y), (rx, py), (px, py)]),
            )
        )

    return BranchNet("operand_corridor", None, junctions, segments)


def _layout_operand_corridor_b(io: Anchor, bottom: list[Anchor]) -> BranchNet:
    """B bus: bottom IO ↑ to row stub Y, horizontal run to 153 B (bottom)."""
    io_x, io_y, _, _, _, _ = _unpack(io)
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []

    stub_ys = [_unpack(g)[5] for g in bottom]
    bus_y = min(stub_ys) if stub_ys else io_y
    tap_xs = [io_x, *(_unpack(g)[4] for g in bottom)]
    x_lo, x_hi = min(tap_xs), max(tap_xs)

    if io_y > bus_y + 0.5:
        segments.append(WireSeg("trunk", "io", [(io_x, io_y), (io_x, bus_y)]))
    segments.append(WireSeg("trunk", "", [(x_lo, bus_y), (x_hi, bus_y)]))

    for anchor in sorted(bottom, key=lambda p: (_unpack(p)[5], _unpack(p)[4])):
        px, py, uid, _, rx, stub_y = _unpack(anchor)
        junctions.append((rx, bus_y, uid))
        segments.append(
            WireSeg(
                "spoke",
                uid,
                _dedupe_xy([(rx, bus_y), (rx, stub_y), (rx, py), (px, py)]),
            )
        )

    return BranchNet("operand_corridor", None, junctions, segments)


def _layout_operand_a(
    io: Anchor, left: list[Anchor], bottom: list[Anchor]
) -> BranchNet:
    """A bus: vertical trunk in 153|283 corridor, row taps to 283 (right) and 153 A (left)."""
    io_x, io_y, _, _, _, _ = _unpack(io)
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []

    row_ys = [_unpack(g)[1] for g in left]
    stub_ys = [_unpack(g)[5] for g in bottom]
    tap_ys = row_ys + stub_ys
    top_y = min(tap_ys) if tap_ys else io_y

    segments.append(WireSeg("trunk", "io", [(io_x, io_y), (io_x, top_y)]))

    for anchor in sorted(bottom, key=lambda p: (_unpack(p)[5], _unpack(p)[4])):
        px, py, uid, _, rx, stub_y = _unpack(anchor)
        junctions.append((io_x, stub_y, uid))
        segments.append(
            WireSeg(
                "spoke",
                uid,
                _dedupe_xy([(io_x, stub_y), (rx, stub_y), (rx, py), (px, py)]),
            )
        )

    for anchor in sorted(left, key=lambda p: _unpack(p)[1]):
        px, py, uid, _, rx, _ = _unpack(anchor)
        junctions.append((io_x, py, uid))
        segments.append(WireSeg("spoke", uid, _dedupe_xy([(io_x, py), (rx, py), (px, py)])))

    return BranchNet("operand_a", None, junctions, segments)


def _layout_bus_mixed(io: Anchor, left: list[Anchor], bottom: list[Anchor], net: str) -> BranchNet:
    """IO horizontal bus for left ports + vertical spine + stub spokes for bottom ports."""
    del net
    io_x, io_y, _, _, _, _ = _unpack(io)
    bus_y = io_y
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []

    trunk_end = io_x
    if left:
        for anchor in left:
            px, _, _, _, rx, _ = _unpack(anchor)
            fork_x = min(rx, px - BRANCH_LEAD)
            trunk_end = max(trunk_end, rx, fork_x)
        segments.append(WireSeg("trunk", "io", [(io_x, bus_y), (trunk_end, bus_y)]))
        for anchor in sorted(left, key=lambda p: _unpack(p)[4]):
            px, py, uid, _, rx, _ = _unpack(anchor)
            junctions.append((rx, bus_y, uid))
            segments.append(WireSeg("spoke", uid, _spoke_left_from_bus(px, py, rx, bus_y)))

    spine_x = max(trunk_end, max(_unpack(g)[4] for g in bottom))
    stub_ys = [_unpack(g)[5] for g in bottom]
    spine_far = max(stub_ys)

    if left and abs(spine_x - trunk_end) > 0.01:
        segments.append(WireSeg("trunk", "", [(trunk_end, bus_y), (spine_x, bus_y)]))
    if not left:
        segments.append(WireSeg("trunk", "io", [(io_x, bus_y), (spine_x, bus_y)]))

    segments.append(WireSeg("trunk", "", [(spine_x, bus_y), (spine_x, spine_far)]))
    for anchor in sorted(bottom, key=lambda p: (_unpack(p)[5], _unpack(p)[4])):
        px, py, uid, _, rx, stub_y = _unpack(anchor)
        junctions.append((spine_x, stub_y, uid))
        segments.append(
            WireSeg("spoke", uid, _spoke_bottom_from_trunk(px, py, rx, spine_x, stub_y))
        )

    return BranchNet("bus_mixed", None, junctions, segments)


def _layout_bus(io: Anchor, gates: list[Anchor], net: str) -> BranchNet:
    left, _, bottom = _partition_sides(gates)
    if left and bottom:
        return _layout_bus_mixed(io, left, bottom, net)

    io_x, io_y, _, _, _, _ = _unpack(io)
    bus_y = io_y
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []

    if left:
        trunk_end = io_x
        for anchor in left:
            px, _, _, _, rx, _ = _unpack(anchor)
            fork_x = min(rx, px - BRANCH_LEAD)
            trunk_end = max(trunk_end, rx, fork_x)
        segments.append(WireSeg("trunk", "io", [(io_x, bus_y), (trunk_end, bus_y)]))
        for anchor in sorted(left, key=lambda p: _unpack(p)[4]):
            px, py, uid, _, rx, _ = _unpack(anchor)
            junctions.append((rx, bus_y, uid))
            segments.append(WireSeg("spoke", uid, _spoke_left_from_bus(px, py, rx, bus_y)))
        return BranchNet("bus_horizontal", None, junctions, segments)

    return _layout_corridor(io, gates, net)


def _layout_corridor(io: Anchor, gates: list[Anchor], net: str) -> BranchNet:
    del net
    io_x, io_y, _, _, _, _ = _unpack(io)
    bottom = sorted([g for g in gates if g[3] == "bottom"], key=lambda p: (_unpack(p)[5], _unpack(p)[4]))
    if not bottom:
        return _layout_star(io, gates, net)
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []
    stub_ys = [_unpack(g)[5] for g in bottom]
    trunk_far = min(stub_ys) if io_y >= max(stub_ys) else max(stub_ys)
    segments.append(WireSeg("trunk", "io", [(io_x, io_y), (io_x, trunk_far)]))
    for anchor in bottom:
        px, py, uid, _, rx, stub_y = _unpack(anchor)
        junctions.append((io_x, stub_y, uid))
        segments.append(
            WireSeg("spoke", uid, _spoke_bottom_from_trunk(px, py, rx, io_x, stub_y))
        )
    return BranchNet("corridor_vertical", None, junctions, segments)


def _column_trunk_x(left: list[Anchor]) -> float:
    return min(_unpack(g)[4] for g in left) - BRANCH_LEAD


def _layout_column_vertical(
    left: list[Anchor], io: Anchor | None = None, net: str = ""
) -> BranchNet:
    """Vertical channel trunk beside a gate column; IO feeder when source is above/below."""
    del net
    junctions: list[tuple[float, float, str]] = []
    segments: list[WireSeg] = []
    ys = [_unpack(g)[1] for g in left]
    port_top = min(ys)
    port_bot = max(ys)
    trunk_x = _column_trunk_x(left)

    if io:
        io_x, io_y, _, _, _, _ = _unpack(io)
        if io_y >= port_bot - 0.5:
            # Source below column (control IO strip)
            if abs(io_x - trunk_x) > 0.01:
                segments.append(WireSeg("trunk", "io", [(io_x, io_y), (trunk_x, io_y)]))
            segments.append(WireSeg("trunk", "", [(trunk_x, port_top), (trunk_x, io_y)]))
        elif io_y <= port_top + 0.5:
            # Source above column
            if abs(io_x - trunk_x) > 0.01:
                segments.append(WireSeg("trunk", "io", [(io_x, io_y), (trunk_x, io_y)]))
            segments.append(WireSeg("trunk", "", [(trunk_x, io_y), (trunk_x, port_bot)]))
        else:
            # Source between rows
            if abs(io_x - trunk_x) > 0.01:
                segments.append(WireSeg("trunk", "io", [(io_x, io_y), (trunk_x, io_y)]))
            segments.append(WireSeg("trunk", "", [(trunk_x, port_top), (trunk_x, port_bot)]))
    else:
        segments.append(WireSeg("trunk", "", [(trunk_x, port_top), (trunk_x, port_bot)]))

    for anchor in sorted(left, key=lambda p: _unpack(p)[1]):
        px, py, uid, _, rx, _ = _unpack(anchor)
        junctions.append((trunk_x, py, uid))
        segments.append(WireSeg("spoke", uid, _spoke_left_from_column(px, py, rx, trunk_x)))
    return BranchNet("column_vertical", None, junctions, segments)


def _layout_star(io: Anchor | None, gates: list[Anchor], net: str) -> BranchNet:
    del net
    if not gates and io:
        return BranchNet("link", None, [], [])
    if gates:
        hub_x = sum(g[0] for g in gates) / len(gates)
        hub_y = sum(g[1] for g in gates) / len(gates)
    else:
        hub_x, hub_y = io[0], io[1]  # type: ignore[index]
    if io and gates:
        hub_x = (io[0] + hub_x) / 2
        hub_y = (io[1] + hub_y) / 2
    hub = (hub_x, hub_y)
    junctions = [(hub_x, hub_y, "hub")]
    segments: list[WireSeg] = []
    endpoints: list[Anchor] = ([io] if io else []) + sorted(gates, key=lambda p: (_unpack(p)[4], p[0]))
    for anchor in endpoints:
        uid = anchor[2]
        pts = _route_to_hub(anchor, hub_x, hub_y)
        segments.append(WireSeg("spoke", uid, pts))
    return BranchNet("star", hub, junctions, segments)


def layout_branch_net(pts: list[Anchor], net: str) -> BranchNet:
    """Build trunk/spoke, corridor, column, hub-star, or direct link layout for one net."""
    if len(pts) < 2:
        return BranchNet("link", None, [], [])

    ios, gates = _split_io_gate(pts)
    if len(ios) >= 2:
        return _layout_star(None, ios + gates, net)
    io = ios[0] if ios else None
    left, _, bottom = _partition_sides(gates)

    if net.startswith("net_b_inv"):
        return _layout_link(pts, net)

    operand = is_b_operand_bit_net(net) or is_a_operand_bit_net(net)
    control = _is_control_net(net)

    if io and operand:
        if is_a_operand_bit_net(net) and left and bottom:
            return _layout_operand_corridor_a(io, left, bottom)
        if is_b_operand_bit_net(net) and bottom:
            return _layout_operand_corridor_b(io, bottom)
        return _layout_bus(io, gates, net)

    if len(pts) == 2:
        return _layout_link(pts, net)

    if io and control:
        if _is_153_left_data_net(net) and left and _is_column_fanout(left):
            return _layout_column_vertical(left, io, net)
        if bottom and left:
            return _layout_bus_mixed(io, left, bottom, net)
        if bottom:
            return _layout_corridor(io, gates, net)
        if left and _is_column_fanout(left):
            return _layout_column_vertical(left, io, net)
        if left:
            return _layout_bus(io, gates, net)

    if not io and left and not bottom:
        if _is_column_fanout(left):
            return _layout_column_vertical(left, None, net)

    if len(gates) == 2 and io is None:
        return _layout_link(pts, net)

    return _layout_star(io, gates, net)
