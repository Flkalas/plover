"""Global gate ??slot assignment (intra- and inter-chip)."""

from __future__ import annotations

import random
from typing import Callable

from hwsim.export_schematic import (
    ASSEMBLY_LAYOUT,
    PinAnchor,
    dip_pin_position,
)
from hwsim.pinout import load_pinout
from hwsim.placement.graph import GateUnit
from hwsim.placement.pack import GateSlot, PartFamily, default_slot_for_ref


def _slot_signal_pin_pos(
    slot: GateSlot,
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict],
    *,
    layout: dict | None = None,
) -> tuple[float, float] | None:
    """Approximate (x,y) of primary signal pin for assignment cost."""
    layout = layout or ASSEMBLY_LAYOUT
    pos = positions.get(slot.package_id)
    if pos is None:
        return None
    bx, by = pos
    part = slot.part if slot.part != "ALU_153_SLICE" else "74HC153"
    po = pinouts.get(part) or load_pinout(part)
    n_pins = int(po.get("package", {}).get("pins", 16))
    body_w = float(layout["body_w"])
    body_h = float(layout["body_h"])
    pin_len = float(layout["pin_len"])
    pin_pitch = layout.get("pin_pitch")

    from hwsim.export_schematic import _logical_to_dip_pin

    if slot.mux is not None:
        # Use mux Y output pin
        logical = f"{slot.mux}Y"
        dip = _logical_to_dip_pin(logical, None, po)
    elif slot.gate is not None:
        dip = _logical_to_dip_pin("Y", slot.gate, po)
        if dip is None:
            dip = _logical_to_dip_pin("A", slot.gate, po)
    else:
        return bx + body_w / 2, by + body_h / 2

    if dip is None:
        return bx + body_w / 2, by + body_h / 2
    x, y, _ = dip_pin_position(
        dip,
        n_pins,
        bx,
        by,
        body_w,
        body_h,
        pin_len,
        pin_pitch=pin_pitch,
    )
    return x, y


def _centroid_for_nets(
    nets: frozenset[str],
    ref_positions: dict[str, tuple[float, float]],
    all_anchors: list[PinAnchor] | None,
) -> tuple[float, float]:
    pts: list[tuple[float, float]] = []
    if all_anchors:
        for a in all_anchors:
            if a.net in nets:
                pts.append((a.x, a.y))
    for _ref, pos in ref_positions.items():
        if pos not in pts:
            pass
    if not pts:
        return 0.0, 0.0
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def assign_cost(
    unit: GateUnit,
    slot: GateSlot,
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict],
    peer_centroids: dict[str, tuple[float, float]],
) -> float:
    sp = _slot_signal_pin_pos(slot, positions, pinouts)
    if sp is None:
        return 1e6
    sx, sy = sp
    total = 0.0
    for net in unit.signal_nets:
        cx, cy = peer_centroids.get(net, (sx, sy))
        total += abs(sx - cx) + abs(sy - cy)
    return total


def _build_peer_centroids(
    units: list[GateUnit],
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict],
    current_assign: dict[str, GateSlot],
    anchors: list[PinAnchor] | None,
) -> dict[str, tuple[float, float]]:
    net_pts: dict[str, list[tuple[float, float]]] = {}
    unit_map = {u.ref: u for u in units}
    for ref, slot in current_assign.items():
        u = unit_map.get(ref)
        if u is None:
            continue
        sp = _slot_signal_pin_pos(slot, positions, pinouts)
        if sp is None:
            continue
        for net in u.signal_nets:
            net_pts.setdefault(net, []).append(sp)
    if anchors:
        for a in anchors:
            if a.net not in net_pts:
                net_pts.setdefault(a.net, []).append((a.x, a.y))
            else:
                net_pts[a.net].append((a.x, a.y))
    return {
        net: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for net, pts in net_pts.items()
    }


def hungarian_assign(
    units: list[GateUnit],
    slots: list[GateSlot],
    cost_fn: Callable[[GateUnit, GateSlot], float],
) -> dict[str, GateSlot]:
    """Heuristic min-cost assignment (greedy + optional local swaps upstream)."""
    n = len(units)
    if n == 0:
        return {}
    if n > len(slots):
        raise ValueError(f"more units ({n}) than slots ({len(slots)})")
    return _greedy_assign(units, slots, cost_fn)


def _greedy_assign(
    units: list[GateUnit],
    slots: list[GateSlot],
    cost_fn: Callable[[GateUnit, GateSlot], float],
) -> dict[str, GateSlot]:
    """Assign each unit to the best remaining slot (heuristic)."""
    remaining_slots = list(slots)
    prios: dict[str, float] = {}
    for u in units:
        costs = sorted(cost_fn(u, s) for s in slots)
        prios[u.ref] = costs[-1] - costs[0] if len(costs) > 1 else costs[0]

    result: dict[str, GateSlot] = {}
    for u in sorted(units, key=lambda x: (-prios[x.ref], x.ref)):
        best: GateSlot | None = None
        best_c = float("inf")
        for s in remaining_slots:
            c = cost_fn(u, s)
            if c < best_c:
                best_c = c
                best = s
        if best is not None:
            result[u.ref] = best
            remaining_slots.remove(best)
    return result


def optimize_gate_assign_for_family(
    family: PartFamily,
    units: list[GateUnit],
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict],
    anchors: list[PinAnchor] | None = None,
    *,
    seed: int = 0,
) -> dict[str, dict[str, str]]:
    """Return package_id ??slot_key ??ref for one part family."""
    fam_units = [u for u in units if u.ref in family.unit_refs]
    if not fam_units:
        return {}

    current: dict[str, GateSlot] = {}
    for u in fam_units:
        s = default_slot_for_ref(u.ref, u.part, [], assembly=True)
        if s is None:
            for slot in family.slots:
                if slot.package_id and u.ref:
                    s = slot
                    break
        if s is not None and s in family.slots:
            current[u.ref] = s

    peer = _build_peer_centroids(fam_units, positions, pinouts, current, anchors)

    def cost_fn(u: GateUnit, slot: GateSlot) -> float:
        return assign_cost(u, slot, positions, pinouts, peer)

    assigned = hungarian_assign(fam_units, family.slots, cost_fn)

    # Local improvement swaps (heuristic polish)
    rng = random.Random(seed)
    refs = list(assigned.keys())
    swap_iters = 40
    for _ in range(swap_iters):
        if len(refs) < 2:
            break
        a, b = rng.sample(refs, 2)
        sa, sb = assigned[a], assigned[b]
        ca = cost_fn(next(u for u in fam_units if u.ref == a), sa) + cost_fn(
            next(u for u in fam_units if u.ref == b), sb
        )
        cb = cost_fn(next(u for u in fam_units if u.ref == a), sb) + cost_fn(
            next(u for u in fam_units if u.ref == b), sa
        )
        if cb < ca:
            assigned[a], assigned[b] = sb, sa

    by_pkg: dict[str, dict[str, str]] = {}
    for ref, slot in assigned.items():
        by_pkg.setdefault(slot.package_id, {})[slot.key] = ref
    return by_pkg


def optimize_all_gate_assign(
    families: dict[str, PartFamily],
    units: list[GateUnit],
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict],
    anchors: list[PinAnchor] | None = None,
    *,
    seed: int = 0,
) -> dict[str, dict[str, dict[str, str]]]:
    out: dict[str, dict[str, dict[str, str]]] = {}
    for part_key, family in families.items():
        out[part_key] = optimize_gate_assign_for_family(
            family, units, positions, pinouts, anchors, seed=seed
        )
    return out


def gate_assign_to_slot_map(
    gate_assign: dict[str, dict[str, dict[str, str]]],
) -> dict[str, GateSlot]:
    """ref ??GateSlot for diff reporting."""
    result: dict[str, GateSlot] = {}
    for part_key, by_pkg in gate_assign.items():
        for pkg_id, slot_map in by_pkg.items():
            for slot_key, ref in slot_map.items():
                if part_key == "ALU_153_SLICE":
                    mux = int(slot_key.replace("mux", ""))
                    result[ref] = GateSlot(
                        package_id=pkg_id, part="74HC153", gate=None, mux=mux
                    )
                else:
                    result[ref] = GateSlot(
                        package_id=pkg_id, part=part_key, gate=int(slot_key)
                    )
    return result
