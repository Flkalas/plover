"""Wire length and layout cost functions."""

from __future__ import annotations

import math
from collections import defaultdict

from hwsim.export_schematic import (
    ASSEMBLY_IO_PANEL_PKG,
    PinAnchor,
    PWR_GND,
    PWR_VCC,
    _is_power_rail,
    _net_hub_center,
    _route_from_panel,
    _route_polyline,
)
from hwsim.placement.graph import external_io_nets
from hwsim.netlist import Netlist

# mm per schematic pixel (approximate for breadboard planning)
PX_TO_MM = 0.35

CRITICAL_SUB_NETS = frozenset(
    {f"net_b{i}" for i in range(8)}
    | {f"net_b_inv{i}" for i in range(8)}
    | {f"net_b_mux{i}" for i in range(8)}
    | {f"net_b_add{i}" for i in range(8)}
    | {f"net_sum{i}" for i in range(8)}
    | {f"net_y{i}" for i in range(8)}
    | {"net_cin", "net_c_lo", "net_c_hi", "net_cin"}
)

CARRY_NETS = frozenset({"net_c_lo"})

IO_BUS_PREFIXES = ("net_a", "net_b", "net_y")


def _net_weight(net: str, io_nets: frozenset[str]) -> float:
    if net in CARRY_NETS:
        return 3.0
    if net in CRITICAL_SUB_NETS and any(
        net.startswith(p) for p in ("net_b", "net_b_inv", "net_b_mux", "net_b_add", "net_sum", "net_y")
    ):
        return 2.5
    if net in io_nets or any(net.startswith(p) for p in IO_BUS_PREFIXES):
        return 1.2
    return 1.0


def polyline_length_mm(points_str: str) -> float:
    pts = [
        tuple(float(v) for v in p.split(","))
        for p in points_str.strip().split()
    ]
    total = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        total += abs(x2 - x1) + abs(y2 - y1)
    return total * PX_TO_MM


def wire_length_for_net(
    net: str,
    anchors: list[PinAnchor],
    *,
    route_stub: float = 56.0,
    stub_step: float = 10.0,
    n_pins: int = 16,
    panel_lane_x: dict[str, float] | None = None,
) -> float:
    if _is_power_rail(net):
        return 0.0
    pts = [a for a in anchors if a.net == net]
    if len(pts) < 2:
        return 0.0
    hx, hy = _net_hub_center(pts)
    total_px = 0.0
    for a in pts:
        if a.package_id == ASSEMBLY_IO_PANEL_PKG:
            lane = (panel_lane_x or {}).get(net, a.x + (40 if a.side == "right" else -40))
            stub = 22.0
            seg = _route_from_panel(a.x, a.y, hx, hy, stub=stub, lane_x=lane, pin_side=a.side)
        else:
            seg = _route_polyline(
                a.x,
                a.y,
                hx,
                hy,
                a.side,
                stub=route_stub,
                dip_pin=a.dip_pin,
                n_pins=n_pins,
                stub_step=stub_step,
            )
        total_px += polyline_length_mm(seg) / PX_TO_MM  # convert back to px for sum
    return total_px * PX_TO_MM


def layout_cost(
    nl: Netlist,
    anchors: list[PinAnchor],
    *,
    io_nets: frozenset[str] | None = None,
    panel_lane_x: dict[str, float] | None = None,
    route_stub: float = 56.0,
    stub_step: float = 10.0,
) -> float:
    io = io_nets if io_nets is not None else external_io_nets(nl)
    nets = {a.net for a in anchors if not _is_power_rail(a.net)}
    total = 0.0
    for net in nets:
        w = _net_weight(net, io)
        total += w * wire_length_for_net(
            net,
            anchors,
            route_stub=route_stub,
            stub_step=stub_step,
            panel_lane_x=panel_lane_x,
        )
    return total


def crossing_proxy(anchors: list[PinAnchor]) -> int:
    """Pin Y-order vs net hub Y-order inversion count (rough crossing estimate)."""
    by_pkg: dict[str, list[PinAnchor]] = defaultdict(list)
    for a in anchors:
        if _is_power_rail(a.net):
            continue
        by_pkg[a.package_id].append(a)
    crossings = 0
    for pts in by_pkg.values():
        ordered = sorted(pts, key=lambda p: p.y)
        hub_ys = sorted(_net_hub_center([p])[1] for p in ordered)
        for i, p in enumerate(ordered):
            hy = _net_hub_center([p])[1]
            if abs(hy - hub_ys[i]) > 8:
                crossings += 1
    return crossings


def net_lengths_mm(
    nl: Netlist,
    anchors: list[PinAnchor],
    *,
    panel_lane_x: dict[str, float] | None = None,
) -> dict[str, float]:
    nets = {a.net for a in anchors if not _is_power_rail(a.net)}
    return {
        net: wire_length_for_net(net, anchors, panel_lane_x=panel_lane_x)
        for net in nets
    }


def sub_path_length_mm(nl: Netlist, anchors: list[PinAnchor], bit: int = 0) -> float:
    """Approximate SUB critical path wire for one bit."""
    path_nets = [f"net_b{bit}", f"net_b_inv{bit}", f"net_b_mux{bit}", f"net_b_add{bit}", f"net_sum{bit}", f"net_y{bit}"]
    lengths = net_lengths_mm(nl, anchors)
    return sum(lengths.get(n, 0.0) for n in path_nets)
