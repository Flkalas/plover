"""Package placement optimizer (simulated annealing + swaps)."""

from __future__ import annotations

import math
import random

from hwsim.export_schematic import ASSEMBLY_LAYOUT, PhysicalPackage, _package_sort_key
from hwsim.netlist import Netlist
from hwsim.placement.anchors import build_anchors, compute_default_positions
from hwsim.placement.cost import crossing_proxy, layout_cost
from hwsim.placement.io_panel import IoPanelSpec, optimize_io_panel


def optimize_positions(
    nl: Netlist,
    packages: list[PhysicalPackage],
    pinouts: dict[str, dict],
    *,
    layout: dict | None = None,
    io_side: str = "left",
    cols: int = 3,
    seed: int = 0,
    iterations: int = 120,
) -> dict[str, tuple[float, float]]:
    layout = layout or ASSEMBLY_LAYOUT
    rng = random.Random(seed)
    sorted_pkgs = sorted(packages, key=_package_sort_key)
    pkg_ids = [p.id for p in sorted_pkgs]

    positions = compute_default_positions(packages, layout, cols=cols, assembly=True)

    def eval_pos(pos: dict[str, tuple[float, float]]) -> float:
        anchors, lane_x = build_anchors(packages, pos, pinouts, layout=layout, nl=nl)
        io_spec = optimize_io_panel(nl, io_side, anchors)
        anchors, lane_x = build_anchors(
            packages, pos, pinouts, layout=layout, io_panel=io_spec, nl=nl
        )
        c = layout_cost(nl, anchors, panel_lane_x=lane_x)
        c += 0.4 * crossing_proxy(anchors)
        return c

    best = dict(positions)
    best_score = eval_pos(best)
    current = dict(best)
    current_score = best_score

    body_w = float(layout["body_w"])
    body_h = float(layout["body_h"])
    gap_x = float(layout["gap_x"])
    gap_y = float(layout["gap_y"])
    pitch_x = body_w + gap_x
    pitch_y = body_h + gap_y

    temp = 200.0
    for _ in range(iterations):
        candidate = dict(current)
        move = rng.randint(0, 2)
        if move == 0 and len(pkg_ids) >= 2:
            a, b = rng.sample(pkg_ids, 2)
            candidate[a], candidate[b] = candidate[b], candidate[a]
        elif move == 1:
            pid = rng.choice(pkg_ids)
            x, y = candidate[pid]
            candidate[pid] = (x + rng.choice([-1, 0, 1]) * pitch_x * 0.25, y)
        else:
            pid = rng.choice(pkg_ids)
            x, y = candidate[pid]
            candidate[pid] = (x, y + rng.choice([-1, 0, 1]) * pitch_y * 0.25)

        cs = eval_pos(candidate)
        delta = cs - current_score
        if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-6)):
            current = candidate
            current_score = cs
            if cs < best_score:
                best = dict(candidate)
                best_score = cs
        temp *= 0.995

    return best
