"""Build KiCad-style schematic HTML viewer from cyclesim functional-block netlists."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from simulators.cyclesim.export.alu8_netlist import (
    build_alu8_func_netlist,
    build_alu8_func_units,
    port_net_names,
)
from simulators.cyclesim.export.schematic_layout import render_alu8_schematic_svg

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VIEWER_KIND = "cyclesim-block"
_ASSETS_DIR = _REPO_ROOT / "viewers" / _VIEWER_KIND / "_assets"
_EMBED_MANIFEST = "/* EMBED_MANIFEST */"
_EMBED_SVG = "/* EMBED_SVG */"

_DRIVE_PIN = re.compile(
    r"^(1Y|2Y|[1-4]Y|S\d*|COUT|Z|C_GE|SEL)$",
    re.IGNORECASE,
)


def _is_drive_pin(pin: str) -> bool:
    return bool(_DRIVE_PIN.match(pin))


def _connection_dir(pin: str) -> str:
    return "drive" if _is_drive_pin(pin) else "load"


def _build_net_connections(
    instances: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    by_net: dict[str, list[dict[str, str]]] = {}
    for inst in instances:
        ref = inst["ref"]
        for pin, net in inst["pins"].items():
            by_net.setdefault(net, []).append(
                {"ref": ref, "pin": pin, "dir": _connection_dir(pin)}
            )
    for conns in by_net.values():
        conns.sort(key=lambda c: (c["ref"], c["pin"]))
    return by_net


def _unit_by_ref(units: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {u["package_ref"]: u for u in units}


def build_block_manifest(
    netlist: dict[str, Any],
    units_doc: dict[str, Any] | None = None,
    *,
    port_names: set[str] | None = None,
    schematic_size: tuple[float, float] | None = None,
) -> dict[str, Any]:
    """Turn netlist (+ optional units) into viewer manifest JSON."""
    instances = netlist["instances"]
    units = units_doc["units"] if units_doc else []
    unit_map = _unit_by_ref(units)
    ports = port_names if port_names is not None else set()

    by_net = _build_net_connections(instances)
    inst_out: dict[str, Any] = {}
    for inst in instances:
        ref = inst["ref"]
        entry: dict[str, Any] = {
            "part": inst["part"],
            "pins": inst["pins"],
        }
        if ref in unit_map:
            u = unit_map[ref]
            entry["unit"] = {
                "id": u["id"],
                "kind": u["kind"],
                "label": u["label"],
                "stage": u["stage"],
            }
        inst_out[ref] = entry

    nets_out: list[dict[str, Any]] = []
    for net in netlist["nets"]:
        name = net["name"]
        conns = by_net.get(name, [])
        drives = [c for c in conns if c["dir"] == "drive"]
        entry: dict[str, Any] = {
            "name": name,
            "width": net.get("width", 1),
            "probes": net.get("probes", []),
            "is_port": name in ports,
            "connections": conns,
            "conflict": len(drives) > 1,
        }
        nets_out.append(entry)

    part_counts: dict[str, int] = {}
    for inst in instances:
        part = inst["part"]
        part_counts[part] = part_counts.get(part, 0) + 1

    manifest: dict[str, Any] = {
        "block": netlist["block"],
        "description": netlist.get("description", ""),
        "nets": nets_out,
        "instances": inst_out,
        "summary": {
            "instance_count": len(instances),
            "net_count": len(nets_out),
            "unit_count": len(units),
            "part_counts": part_counts,
        },
    }
    if schematic_size is not None:
        manifest["schematic"] = {"width": schematic_size[0], "height": schematic_size[1]}
    return manifest


def build_alu8_func_viewer_payload() -> tuple[dict[str, Any], str]:
    netlist = build_alu8_func_netlist()
    units = build_alu8_func_units()
    ports = port_net_names()
    svg, w, h = render_alu8_schematic_svg(netlist, port_names=ports)
    manifest = build_block_manifest(
        netlist,
        units,
        port_names=ports,
        schematic_size=(w, h),
    )
    return manifest, svg


def build_alu8_func_manifest() -> dict[str, Any]:
    manifest, _ = build_alu8_func_viewer_payload()
    return manifest


def default_html_out(block_name: str) -> Path:
    return _REPO_ROOT / "viewers" / _VIEWER_KIND / block_name / "index.html"


def _self_contained_html(manifest: dict[str, Any], svg: str) -> str:
    template = (_ASSETS_DIR / "block-viewer.html").read_text(encoding="utf-8")
    css = (_ASSETS_DIR / "block-viewer.css").read_text(encoding="utf-8")
    js = (_ASSETS_DIR / "block-viewer.js").read_text(encoding="utf-8")
    payload = json.dumps(manifest, ensure_ascii=False)
    html = template.replace(
        '<link rel="stylesheet" href="block-viewer.css">',
        f"<style>\n{css}\n</style>",
    )
    html = html.replace(
        '<script src="block-viewer.js"></script>',
        f"<script>\n{js}\n</script>",
    )
    if _EMBED_MANIFEST not in html:
        raise ValueError(f"template missing {_EMBED_MANIFEST}")
    if _EMBED_SVG not in html:
        raise ValueError(f"template missing {_EMBED_SVG}")
    html = html.replace(_EMBED_MANIFEST, payload)
    return html.replace(_EMBED_SVG, svg)


def write_block_viewer_html(
    manifest: dict[str, Any],
    svg: str,
    out_path: Path,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_self_contained_html(manifest, svg), encoding="utf-8")
    return out_path


def export_alu8_block_viewer(html_out: Path | None = None) -> Path:
    manifest, svg = build_alu8_func_viewer_payload()
    path = html_out if html_out is not None else default_html_out(manifest["block"])
    return write_block_viewer_html(manifest, svg, path)


def export_block_viewer_for(
    block_name: str,
    html_out: Path | None = None,
) -> Path:
    builders: dict[str, Callable[[], tuple[dict[str, Any], str]]] = {
        "alu8_func": build_alu8_func_viewer_payload,
    }
    if block_name not in builders:
        raise ValueError(f"unknown block for viewer export: {block_name}")
    manifest, svg = builders[block_name]()
    path = html_out if html_out is not None else default_html_out(block_name)
    return write_block_viewer_html(manifest, svg, path)
