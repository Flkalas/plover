"""Channel-based orthogonal router for ALU8 schematic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from simulators.cyclesim.export.schematic.alu8_template import (
    A_ROW_OFFSET,
    B_ROW_OFFSET,
    BUS_BOTTOM,
    BUS_CTRL_LEFT,
    BUS_TOP,
    GRID,
    ORPHAN_PORTS,
    ROW_GAP,
    ROW_PITCH,
    Alu8Template,
    chip_obstacles,
    snap,
    stub_tip,
)
from simulators.cyclesim.export.schematic.types import PinAnchor

PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"
LANE_SPACING = GRID * 5
STUB_OUT = GRID * 3
PIN_PITCH = GRID * 2


def chip_anchors(anchors: list[PinAnchor]) -> list[PinAnchor]:
    return [a for a in anchors if a.ref != "__port__"]


def port_anchors(anchors: list[PinAnchor]) -> list[PinAnchor]:
    return [a for a in anchors if a.ref == "__port__"]


@dataclass
class ChannelRoutePlan:
    ch_x: float
    trunk_y: float
    anchors: dict[tuple[str, str], Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteContext:
    tmpl: Alu8Template
    bus_rails: dict[str, float]
    channel_plans: dict[str, ChannelRoutePlan]
    obstacles: list[tuple[float, float, float, float]]


def _alloc_line(preferred: float, used: set[float], step: float = GRID) -> float:
    base = snap(preferred)
    if base not in used:
        used.add(base)
        return base
    offset = step
    while True:
        for candidate in (base + offset, base - offset):
            snapped = snap(candidate)
            if snapped not in used:
                used.add(snapped)
                return snapped
        offset += step


def _net_bit(net: str) -> int | None:
    if net.startswith("net_a") or net.startswith("net_b"):
        return int(net[-1])
    if net.startswith("net_y") and not net.startswith("net_y_logic") and net != "net_y_mux_sel":
        return int(net[-1])
    if net.startswith("net_b_add") or net.startswith("net_sum") or net.startswith("net_y_logic"):
        return int(net[-1])
    return None


def _channel_base(net: str, tmpl: Alu8Template) -> float:
    if net.startswith("net_c_") or net == "net_cin":
        return tmpl.ch_153_283
    if net.startswith("net_y") and not net.startswith("net_y_logic") and not net.startswith("net_y_mux"):
        return tmpl.ch_283_157
    if net.startswith("net_sum") or net.startswith("net_y_logic"):
        return tmpl.ch_283_157 - LANE_SPACING * 2
    return tmpl.ch_153_283 + LANE_SPACING * 2


def _anchor_centroid(anchors: list[PinAnchor]) -> tuple[float, float]:
    xs = [a.x for a in anchors]
    ys = [a.y for a in anchors]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _gap_before(col_x: float) -> float:
    return snap(col_x - GRID * 2)


def _bus_spine_x(net: str, tmpl: Alu8Template) -> float:
    idx = int(net[-1]) if net[-1].isdigit() else 0
    if net in BUS_TOP:
        return snap(tmpl.col_153 + tmpl.body_w_153 + GRID * (2 + idx))
    if net in BUS_BOTTOM:
        return snap(tmpl.col_153 - GRID * (4 + idx))
    return snap(tmpl.port_tap_x)


def build_route_assignments(
    by_net: dict[str, list[PinAnchor]],
    tmpl: Alu8Template,
    port_names: set[str],
) -> tuple[dict[str, ChannelRoutePlan], dict[str, float], dict[str, float], dict]:
    """Assign channel trunks and bus rail Y coordinates."""
    used_x: set[float] = set()
    used_y: set[float] = set()
    channel_plans: dict[str, ChannelRoutePlan] = {}
    bus_rails: dict[str, float] = {}
    bus_vrail_x: dict[str, float] = {}

    for net in sorted(BUS_TOP):
        bus_rails[net] = tmpl.lgc_rail_y[net]
    for net in sorted(BUS_BOTTOM):
        bus_rails[net] = tmpl.bctrl_rail_y[net]
    for net, y in tmpl.ctrl_rail_y.items():
        bus_rails[net] = y
    bus_rails["net_y_mux_sel"] = tmpl.y_mux_rail_y
    for net, y in tmpl.flag_rail_y.items():
        bus_rails[net] = y

    channel_groups: dict[float, list[str]] = {}
    for net, anchors in by_net.items():
        if net in BUS_TOP | BUS_BOTTOM | BUS_CTRL_LEFT | {"net_y_mux_sel"}:
            continue
        if net in (PWR_VCC, PWR_GND) or net in ORPHAN_PORTS:
            continue
        chips = chip_anchors(anchors)
        if len(chips) < 2:
            continue
        base = _channel_base(net, tmpl)
        channel_groups.setdefault(base, []).append(net)

    for base in sorted(channel_groups):
        nets = channel_groups[base]
        nets.sort(key=lambda n: _anchor_centroid(chip_anchors(by_net[n])))
        for i, net in enumerate(nets):
            anchors = chip_anchors(by_net[net])
            cx, cy = _anchor_centroid(anchors)
            preferred_x = base + (i - (len(nets) - 1) / 2) * LANE_SPACING
            ch_x = _alloc_line(preferred_x, used_x)
            bit = _net_bit(net)
            if bit is not None:
                if net.startswith("net_b_add"):
                    base_y = tmpl.row_y[bit] + B_ROW_OFFSET
                elif net.startswith("net_sum") or net.startswith("net_y"):
                    base_y = tmpl.row_y[bit] + A_ROW_OFFSET
                else:
                    base_y = tmpl.row_y[bit] + A_ROW_OFFSET
                trunk_y = _alloc_line(base_y, used_y)
            else:
                trunk_y = _alloc_line(cy, used_y)
            channel_plans[net] = ChannelRoutePlan(ch_x=ch_x, trunk_y=trunk_y)

    return channel_plans, bus_rails, bus_vrail_x, {}


def _h_path(x0: float, y: float, x1: float) -> list[tuple[float, float]]:
    if x0 > x1:
        x0, x1 = x1, x0
    return [(x0, y), (x1, y)]


def _append_segment(
    points: list[tuple[float, float]],
    x: float,
    y: float,
) -> None:
    if not points:
        points.append((x, y))
        return
    lx, ly = points[-1]
    if abs(lx - x) < 0.1 and abs(ly - y) < 0.1:
        return
    points.append((x, y))


def _route_row_tap(
    anchors: list[PinAnchor],
    tmpl: Alu8Template,
) -> list[list[tuple[float, float]]]:
    ports = port_anchors(anchors)
    chips = chip_anchors(anchors)
    if not ports or not chips:
        return []
    port = ports[0]
    chip = min(chips, key=lambda a: abs(a.y - port.y))
    sx, sy = stub_tip(chip)
    return [_h_path(port.x, port.y, sx)]


def _chain_vertical(x: float, y0: float, y1: float) -> list[list[tuple[float, float]]]:
    if abs(y0 - y1) < GRID:
        return []
    if y0 > y1:
        y0, y1 = y1, y0
    segs: list[list[tuple[float, float]]] = []
    y = y0
    while y + ROW_PITCH < y1:
        segs.append([(x, y), (x, y + ROW_PITCH)])
        y += ROW_PITCH
    if y < y1:
        segs.append([(x, y), (x, y1)])
    return segs


def _chip_row_index(ref: str) -> int | None:
    if ref.startswith("U_ALU_153_"):
        return int(ref.split("_")[-1])
    return None


def _bus_tap_y(anchor: PinAnchor, tmpl: Alu8Template, *, top: bool) -> float:
    row_i = _chip_row_index(anchor.ref)
    if row_i is not None:
        base = tmpl.row_y[row_i]
        if top:
            if row_i > 0:
                return snap((tmpl.row_y[row_i - 1] + tmpl.body_h_153 + base) / 2)
            return snap(base - STUB_OUT)
        if row_i < 7:
            return snap((base + tmpl.body_h_153 + tmpl.row_y[row_i + 1]) / 2)
        return snap(base + tmpl.body_h_153 + ROW_GAP / 2)
    if top:
        return snap(anchor.y - STUB_OUT)
    return snap(anchor.y + STUB_OUT)


def _route_horiz_bus(
    net: str,
    anchors: list[PinAnchor],
    tmpl: Alu8Template,
    rail_y: float,
) -> list[list[tuple[float, float]]]:
    """Horizontal bus with row-level taps via corridor spine (short vertical segments)."""
    chips = sorted(chip_anchors(anchors), key=lambda a: (a.y, a.x))
    ports = port_anchors(anchors)
    if not chips and not ports:
        return []

    spine_x = _bus_spine_x(net, tmpl)
    paths: list[list[tuple[float, float]]] = []

    for port in ports:
        paths.append(_h_path(port.x, rail_y, spine_x))

    tap_ys: list[float] = []
    top_side = net in BUS_TOP

    for anchor in chips:
        sx, sy = stub_tip(anchor)
        bus_y = _bus_tap_y(anchor, tmpl, top=top_side)
        tap_ys.append(bus_y)
        route_y = bus_y
        points: list[tuple[float, float]] = [(sx, sy)]
        if abs(sy - route_y) > GRID:
            _append_segment(points, anchor.x, route_y)
        if anchor.x != spine_x:
            _append_segment(points, spine_x, route_y)
        paths.append(points)

    chain_ys = sorted(set(tap_ys + [rail_y]))
    for i in range(len(chain_ys) - 1):
        paths.extend(_chain_vertical(spine_x, chain_ys[i], chain_ys[i + 1]))

    return paths


def _route_horiz_ctrl(
    net: str,
    anchors: list[PinAnchor],
    tmpl: Alu8Template,
    rail_y: float,
) -> list[list[tuple[float, float]]]:
    chips = chip_anchors(anchors)
    ports = port_anchors(anchors)
    gap_x = _gap_before(tmpl.col_283)
    x_right = snap(tmpl.col_283 + GRID)
    paths: list[list[tuple[float, float]]] = [_h_path(tmpl.port_tap_x, rail_y, x_right)]

    for anchor in chips:
        sx, sy = stub_tip(anchor)
        points: list[tuple[float, float]] = [(sx, sy)]
        if anchor.side == "left":
            _append_segment(points, gap_x, sy)
            _append_segment(points, gap_x, rail_y)
        else:
            _append_segment(points, anchor.x, rail_y)
        paths.append(points)

    for port in ports:
        if abs(port.y - rail_y) < GRID:
            paths.append(_h_path(port.x, port.y, tmpl.port_tap_x))
        else:
            paths.append([(port.x, port.y), (port.x, rail_y)])

    return paths


def _route_y_mux(
    anchors: list[PinAnchor],
    tmpl: Alu8Template,
    rail_y: float,
) -> list[list[tuple[float, float]]]:
    chips = sorted(chip_anchors(anchors), key=lambda a: (a.y, a.ref))
    ports = port_anchors(anchors)
    gap_x = _gap_before(tmpl.col_157)
    x_right = snap(tmpl.col_157 + GRID * 6)
    paths: list[list[tuple[float, float]]] = [_h_path(tmpl.port_tap_x, rail_y, x_right)]

    for port in ports:
        if abs(port.y - rail_y) < GRID:
            paths.append(_h_path(port.x, port.y, tmpl.port_tap_x))
        else:
            paths.append([(port.x, port.y), (port.x, rail_y)])

    for anchor in chips:
        sx, sy = stub_tip(anchor)
        row_i = 4 if anchor.ref == "U_ALU_157_YBP_1" else 0
        if row_i == 0:
            route_y = snap(tmpl.row_y[0] - STUB_OUT)
        else:
            block_h = ROW_PITCH * 4 - ROW_GAP
            route_y = snap((tmpl.row_y[0] + block_h + tmpl.row_y[4]) / 2)
        points: list[tuple[float, float]] = [(sx, sy)]
        if abs(sy - route_y) > GRID:
            _append_segment(points, anchor.x, route_y)
        _append_segment(points, gap_x, route_y)
        if abs(route_y - rail_y) > GRID:
            _append_segment(points, gap_x, rail_y)
        if abs(gap_x - anchor.x) > GRID:
            _append_segment(points, anchor.x, rail_y)
        paths.append(points)
    return paths


def _pick_gap_x(a: PinAnchor, b: PinAnchor, tmpl: Alu8Template) -> float:
    lo = min(a.x, b.x)
    hi = max(a.x, b.x)
    if hi <= tmpl.col_153 + tmpl.body_w_153 + GRID:
        return tmpl.ch_153_283
    if lo < tmpl.col_283 and hi >= tmpl.col_283:
        return _gap_before(tmpl.col_283)
    if lo < tmpl.col_157 and hi >= tmpl.col_157:
        return _gap_before(tmpl.col_157)
    if hi <= tmpl.col_283 + GRID * 14:
        return tmpl.ch_153_283
    return tmpl.ch_283_157


def _backbone_y(tmpl: Alu8Template) -> float:
    return snap(tmpl.row_y[7] + tmpl.body_h_153 + ROW_GAP * 2)


def _link_two_pins(
    a: PinAnchor,
    b: PinAnchor,
    tmpl: Alu8Template,
) -> list[tuple[float, float]]:
    """Route between two pins via column gaps and a below-stack backbone."""
    sx, sy = stub_tip(a)
    dx, dy = stub_tip(b)
    gap_a = _gap_before(tmpl.col_283) if a.x < tmpl.col_283 else _gap_before(tmpl.col_157)
    gap_b = _gap_before(tmpl.col_157) if b.x >= tmpl.col_157 else _gap_before(tmpl.col_283)
    if a.x >= tmpl.col_283:
        gap_a = _gap_before(tmpl.col_157)
    if b.x < tmpl.col_283:
        gap_b = _gap_before(tmpl.col_283)
    if abs(a.x - b.x) < GRID * 4:
        gap_a = gap_b = _pick_gap_x(a, b, tmpl)

    backbone = _backbone_y(tmpl)
    points: list[tuple[float, float]] = [(sx, sy)]

    if a.side == "right":
        _append_segment(points, snap(sx + STUB_OUT), sy)
    elif a.side == "left":
        _append_segment(points, snap(sx - STUB_OUT), sy)
    elif a.side == "top":
        _append_segment(points, sx, snap(sy - STUB_OUT))
        sy = snap(sy - STUB_OUT)
    else:
        _append_segment(points, sx, snap(sy + STUB_OUT))
        sy = snap(sy + STUB_OUT)

    _append_segment(points, gap_a, sy)
    if abs(sy - backbone) > GRID:
        _append_segment(points, gap_a, backbone)
    if gap_a != gap_b and abs(gap_a - gap_b) > GRID:
        _append_segment(points, gap_b, backbone)
    if abs(backbone - dy) > GRID:
        _append_segment(points, gap_b, dy)

    if b.side == "left":
        entry_x = snap(dx - STUB_OUT)
        if entry_x > gap_b:
            _append_segment(points, entry_x, dy)
    elif b.side == "right":
        _append_segment(points, snap(dx + STUB_OUT), dy)
    elif b.side == "top":
        _append_segment(points, dx, snap(dy - STUB_OUT))
        dy = snap(dy - STUB_OUT)
    else:
        _append_segment(points, dx, snap(dy + STUB_OUT))
        dy = snap(dy + STUB_OUT)

    _append_segment(points, dx, dy)
    return points


def _route_channel_net(
    anchors: list[PinAnchor],
    plan: ChannelRoutePlan,
    tmpl: Alu8Template,
) -> list[list[tuple[float, float]]]:
    chips = sorted(chip_anchors(anchors), key=lambda a: (a.y, a.x, a.ref))
    if len(chips) < 2:
        return []
    if len(chips) == 2:
        return [_link_two_pins(chips[0], chips[1], tmpl)]

    paths: list[list[tuple[float, float]]] = []
    hub = chips[0]
    for other in chips[1:]:
        paths.append(_link_two_pins(hub, other, tmpl))
    return paths


def _route_port_tap(
    net: str,
    anchors: list[PinAnchor],
    plan: ChannelRoutePlan,
    tmpl: Alu8Template,
) -> list[list[tuple[float, float]]]:
    if net.startswith("net_a") or net.startswith("net_b"):
        return _route_row_tap(anchors, tmpl)

    paths = _route_channel_net(anchors, plan, tmpl)
    ports = port_anchors(anchors)
    chips = chip_anchors(anchors)
    if not ports:
        return paths

    port = ports[0]
    if net.startswith("net_y") and net not in {"net_y_mux_sel"} and not net.startswith("net_y_logic"):
        chip = min(chips, key=lambda a: abs(a.y - port.y))
        sx, _ = stub_tip(chip)
        paths.append(_h_path(sx, port.y, tmpl.port_x_right))
        return paths

    if net in tmpl.flag_rail_y or net == "net_c_hi":
        paths.append(_h_path(tmpl.port_tap_x, port.y, tmpl.port_x_right))
        return paths

    paths.append([(tmpl.port_tap_x, port.y), (plan.ch_x, port.y), (plan.ch_x, plan.trunk_y)])
    return paths


def _route_orphan_port(net: str, tmpl: Alu8Template) -> list[list[tuple[float, float]]]:
    if net in tmpl.ctrl_rail_y:
        y = tmpl.ctrl_rail_y[net]
        return [_h_path(tmpl.port_x_ctrl, y, tmpl.port_tap_x + GRID * 4)]
    if net in tmpl.flag_rail_y:
        y = tmpl.flag_rail_y[net]
        return [_h_path(tmpl.port_tap_x, y, tmpl.port_x_right)]
    return []


def route_net(
    net: str,
    anchors: list[PinAnchor],
    ctx: RouteContext,
    port_names: set[str],
) -> list[list[tuple[float, float]]]:
    if net in (PWR_VCC, PWR_GND):
        return []
    if net in ORPHAN_PORTS and not chip_anchors(anchors):
        return _route_orphan_port(net, ctx.tmpl)

    rail_y = ctx.bus_rails.get(net)
    if net in BUS_TOP | BUS_BOTTOM:
        if rail_y is not None:
            return _route_horiz_bus(net, anchors, ctx.tmpl, rail_y)
    if net in BUS_CTRL_LEFT:
        if rail_y is not None:
            return _route_horiz_ctrl(net, anchors, ctx.tmpl, rail_y)
    if net == "net_y_mux_sel":
        return _route_y_mux(anchors, ctx.tmpl, ctx.bus_rails.get(net, ctx.tmpl.y_mux_rail_y))

    if net.startswith("net_a") or net.startswith("net_b"):
        if port_names and net in port_names:
            return _route_row_tap(anchors, ctx.tmpl)

    plan = ctx.channel_plans.get(net)
    if plan:
        if net in port_names:
            return _route_port_tap(net, anchors, plan, ctx.tmpl)
        return _route_channel_net(anchors, plan, ctx.tmpl)

    if len(anchors) == 1:
        a = anchors[0]
        sx, sy = stub_tip(a)
        return [[(sx, sy)]]
    return []


def route_all(
    by_net: dict[str, list[PinAnchor]],
    tmpl: Alu8Template,
    instances: list[dict],
    port_names: set[str],
) -> dict[str, list[list[tuple[float, float]]]]:
    channel_plans, bus_rails, _, _ = build_route_assignments(by_net, tmpl, port_names)
    ctx = RouteContext(
        tmpl=tmpl,
        bus_rails=bus_rails,
        channel_plans=channel_plans,
        obstacles=chip_obstacles(instances),
    )
    out: dict[str, list[list[tuple[float, float]]]] = {}
    for net, anchors in by_net.items():
        if net in (PWR_VCC, PWR_GND):
            continue
        paths = route_net(net, anchors, ctx, port_names)
        if not paths and net in ORPHAN_PORTS:
            paths = _route_orphan_port(net, ctx.tmpl)
        out[net] = paths
    return out


def segment_intersects_rect(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
) -> bool:
    """Check if orthogonal segment intersects rectangle interior."""
    if y0 == y1:
        if y0 <= ry or y0 >= ry + rh:
            return False
        seg_x0, seg_x1 = min(x0, x1), max(x0, x1)
        return seg_x1 > rx and seg_x0 < rx + rw
    if x0 == x1:
        if x0 <= rx or x0 >= rx + rw:
            return False
        seg_y0, seg_y1 = min(y0, y1), max(y0, y1)
        return seg_y1 > ry and seg_y0 < ry + rh
    return False


def paths_hit_obstacles(
    paths: list[list[tuple[float, float]]],
    obstacles: list[tuple[float, float, float, float]],
) -> bool:
    for path in paths:
        for i in range(len(path) - 1):
            x0, y0 = path[i]
            x1, y1 = path[i + 1]
            for rx, ry, rw, rh in obstacles:
                if segment_intersects_rect(x0, y0, x1, y1, rx, ry, rw, rh):
                    return True
    return False
