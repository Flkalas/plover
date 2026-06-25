"""Batch export gate-level unit schematics + full gate connectivity graph."""

from __future__ import annotations

import json
from pathlib import Path

from hwsim.export_gate_graph import export_gate_graph_html, export_gate_graph_svg
from hwsim.export_gate_schematic import export_gate_schematic_html, export_gate_schematic_svg
from hwsim.netlist import load_netlist
from hwsim.units.catalog import CATEGORY_LABELS, ViewUnit, load_alu8_catalog, validate_catalog
from hwsim.units.scope import scope_to_manifest_entry, unit_scope

_UNITS_VIEWER_MARKER = "/* EMBED_MANIFEST */"


def export_units(
    netlist_path: Path,
    *,
    output_dir: Path,
    html: bool = False,
    unit_id: str | None = None,
    embed_manifest: bool = False,
) -> dict:
    nl = load_netlist(netlist_path)
    all_units = load_alu8_catalog()
    errors = validate_catalog(nl, all_units)
    if errors:
        raise ValueError("catalog validation failed:\n" + "\n".join(errors))

    units = all_units
    if unit_id:
        units = [u for u in all_units if u.id == unit_id]
        if not units:
            raise ValueError(f"unknown unit id: {unit_id}")

    output_dir.mkdir(parents=True, exist_ok=True)

    graph_svg = export_gate_graph_svg(nl, all_units)
    graph_svg_path = output_dir / "alu8-gates.svg"
    graph_svg_path.write_text(graph_svg, encoding="utf-8")

    graph_html_name = "alu8-gates.html"
    if html:
        (output_dir / graph_html_name).write_text(export_gate_graph_html(nl), encoding="utf-8")

    entries: list[dict] = []
    for unit in all_units:
        scope = unit_scope(nl, unit)
        entry = {
            "id": unit.id,
            "kind": unit.kind,
            "category": unit.category(),
            "label": unit.label,
            "stage": unit.stage,
            **scope_to_manifest_entry(scope),
        }
        if unit_id is None or unit.id == unit_id:
            svg_path = output_dir / f"{unit.id}.svg"
            svg_path.write_text(export_gate_schematic_svg(nl, unit), encoding="utf-8")
            entry["svg"] = svg_path.name
            if html:
                html_path = output_dir / f"{unit.id}.html"
                html_path.write_text(export_gate_schematic_html(nl, unit), encoding="utf-8")
                entry["html"] = html_path.name
        entries.append(entry)

    manifest = {
        "block": nl.block,
        "source": str(netlist_path).replace("\\", "/"),
        "view": "gate",
        "graph_svg": graph_svg_path.name,
        "graph_html": graph_html_name if html else None,
        "categories": [
            {"kind": kind, "label": label}
            for kind, label in CATEGORY_LABELS.items()
        ],
        "units": entries,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if embed_manifest:
        repo = Path(__file__).resolve().parents[2]
        viewer_src = repo / "hw" / "viewer" / "units.html"
        graph_filter_js = (repo / "hw" / "viewer" / "gate-graph-filter.js").read_text(
            encoding="utf-8"
        )
        interactive_js = (repo / "hw" / "viewer" / "schematic-interactive.js").read_text(
            encoding="utf-8"
        )
        text = viewer_src.read_text(encoding="utf-8")
        text = text.replace('<script src="schematic-interactive.js"></script>', "")
        text = text.replace('<script src="gate-graph-filter.js"></script>', "")
        payload = f"window.__UNITS_MANIFEST__ = {json.dumps(manifest)};"
        if _UNITS_VIEWER_MARKER in text:
            text = text.replace(_UNITS_VIEWER_MARKER, payload)
        embedded = output_dir / "index.html"
        embedded.write_text(
            text.replace(
                "</body>",
                f"<script>\n{graph_filter_js}\n</script>\n"
                f"<script>\n{interactive_js}\n</script>\n</body>",
            ),
            encoding="utf-8",
        )
        manifest["viewer"] = embedded.name

    return manifest


def format_unit_list(units: list[ViewUnit]) -> str:
    lines = [f"{'id':<16} {'kind':<10} stage  label", "-" * 56]
    for u in units:
        lines.append(f"{u.id:<16} {u.kind:<10} {u.stage:<5}  {u.label}")
    lines.append(f"\nTotal: {len(units)} units")
    return "\n".join(lines)
