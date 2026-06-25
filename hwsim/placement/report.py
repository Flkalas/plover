"""CLI report formatting."""

from __future__ import annotations

from hwsim.placement.cost import layout_cost, net_lengths_mm, sub_path_length_mm, crossing_proxy
from hwsim.placement.layout_spec import LayoutDocument, VariantLayout
from hwsim.placement.pack import GateSlot, default_gate_assign, default_slot_for_ref
from hwsim.export_schematic import PinAnchor
from hwsim.netlist import Netlist
from hwsim.placement.graph import GateUnit


def format_report(
    nl: Netlist,
    doc: LayoutDocument,
    *,
    default_cost: float | None = None,
    units: list[GateUnit] | None = None,
    packages: list | None = None,
    assembly: bool = True,
) -> str:
    lines: list[str] = []
    lines.append(f"=== Layout optimization: {doc.block} ({doc.mode}) ===")
    lines.append("")

    if len(doc.variants) >= 2:
        lines.append("Variant comparison (abstract wire mm):")
        for vname, var in doc.variants.items():
            m = var.metrics
            tw = m.get("total_wire_mm", {})
            ab = tw.get("abstract", "?")
            lines.append(
                f"  {vname}: wire {ab} mm  crossings {m.get('crossings', '?')}  "
                f"SUB path {m.get('critical_sub_path_mm', '?')} mm"
            )
        lines.append("")

    for vname, var in doc.variants.items():
        lines.append(f"--- {vname} ---")
        m = var.metrics
        tw = m.get("total_wire_mm", {})
        ab = tw.get("abstract", tw)
        if default_cost is not None and isinstance(ab, (int, float)):
            pct = (1 - ab / default_cost) * 100 if default_cost else 0
            lines.append(f"Total wire (abstract): {ab} mm  [{pct:+.0f}% vs default grid]")
        else:
            lines.append(f"Total wire (abstract): {ab} mm")
        lines.append(f"Crossings: {m.get('crossings', '?')}")
        lines.append(f"Critical SUB path: {m.get('critical_sub_path_mm', '?')} mm")
        lines.append("")

        top = m.get("top_nets", [])
        if top:
            lines.append("Top longest nets:")
            for entry in top[:10]:
                lines.append(f"  {entry}")
            lines.append("")

        moves = m.get("gate_moves", [])
        if moves:
            lines.append("Gate reassignments:")
            for mv in moves[:20]:
                lines.append(f"  {mv}")
            lines.append("")

    return "\n".join(lines)


def gate_move_summary(
    nl: Netlist,
    units: list[GateUnit],
    packages: list,
    optimized: dict[str, dict[str, dict[str, str]]],
    *,
    assembly: bool,
) -> list[str]:
    default = default_gate_assign(nl, units, packages, assembly=assembly)
    opt_slots: dict[str, GateSlot] = {}
    for part_key, by_pkg in optimized.items():
        for pkg_id, slot_map in by_pkg.items():
            for slot_key, ref in slot_map.items():
                if part_key == "ALU_153_SLICE":
                    opt_slots[ref] = GateSlot(pkg_id, "74HC153", None, int(slot_key.replace("mux", "")))
                else:
                    opt_slots[ref] = GateSlot(pkg_id, part_key, int(slot_key))

    def_slots: dict[str, GateSlot] = {}
    for part_key, by_pkg in default.items():
        for pkg_id, slot_map in by_pkg.items():
            for slot_key, ref in slot_map.items():
                if part_key == "ALU_153_SLICE":
                    def_slots[ref] = GateSlot(pkg_id, "74HC153", None, int(slot_key.replace("mux", "")))
                else:
                    def_slots[ref] = GateSlot(pkg_id, part_key, int(slot_key))

    lines: list[str] = []
    moved = 0
    for ref, opt in opt_slots.items():
        d = def_slots.get(ref)
        if d is None:
            continue
        same = d.package_id == opt.package_id and d.key == opt.key
        if not same:
            moved += 1
            kind = "inter-chip" if d.package_id != opt.package_id else "intra-chip"
            lines.append(
                f"{ref}: {d.package_id} slot {d.key} ??{opt.package_id} slot {opt.key} ({kind})"
            )
    if lines:
        lines.append(f"... {moved} moved, {len(opt_slots) - moved} unchanged")
    return lines


def compute_variant_metrics(
    nl: Netlist,
    anchors: list[PinAnchor],
    panel_lane_x: dict[str, float] | None = None,
) -> dict:
    lengths = net_lengths_mm(nl, anchors, panel_lane_x=panel_lane_x)
    top = sorted(lengths.items(), key=lambda x: -x[1])[:10]
    top_lines = [f"{net}  {mm:.1f} mm" for net, mm in top]
    return {
        "total_wire_mm": {"abstract": round(layout_cost(nl, anchors, panel_lane_x=panel_lane_x), 1)},
        "crossings": crossing_proxy(anchors),
        "critical_sub_path_mm": round(sub_path_length_mm(nl, anchors), 1),
        "top_nets": top_lines,
    }
