"""Block viewer export tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

from simulators.cyclesim.export.block_viewer import (
    build_alu8_func_manifest,
    build_alu8_func_viewer_payload,
    export_alu8_block_viewer,
    write_block_viewer_html,
)


def _net(manifest: dict, name: str) -> dict:
    for net in manifest["nets"]:
        if net["name"] == name:
            return net
    raise KeyError(name)


def _conn_refs(net: dict) -> list[tuple[str, str]]:
    return [(c["ref"], c["pin"]) for c in net["connections"]]


def test_manifest_net_count() -> None:
    manifest = build_alu8_func_manifest()
    assert manifest["summary"]["net_count"] == len(manifest["nets"])
    assert manifest["summary"]["net_count"] == 66
    assert manifest["summary"]["instance_count"] == 20
    assert manifest["schematic"]["width"] > 0
    assert manifest["schematic"]["height"] > 0


def test_net_b_add0_connections() -> None:
    net = _net(build_alu8_func_manifest(), "net_b_add0")
    refs = _conn_refs(net)
    assert ("U_MUX4_0", "Y_BADD") in refs
    assert ("U_ADD_LO", "B0") in refs


def test_net_c_lo_drive_and_load() -> None:
    net = _net(build_alu8_func_manifest(), "net_c_lo")
    by_ref = {c["ref"]: c for c in net["connections"]}
    assert by_ref["U_ADD_LO"]["dir"] == "drive"
    assert by_ref["U_ADD_LO"]["pin"] == "COUT"
    assert by_ref["U_ADD_HI"]["dir"] == "load"
    assert by_ref["U_ADD_HI"]["pin"] == "CIN"


def test_port_net_flag() -> None:
    net = _net(build_alu8_func_manifest(), "net_a0")
    assert net["is_port"] is True


def test_export_html_embeds_manifest_and_svg(tmp_path: Path) -> None:
    out = tmp_path / "index.html"
    export_alu8_block_viewer(out)
    text = out.read_text(encoding="utf-8")
    assert "/* EMBED_MANIFEST */" not in text
    assert "/* EMBED_SVG */" not in text
    assert "<svg" in text
    assert "id=\"net-groups\"" not in text
    assert "const MANIFEST =" in text
    match = re.search(r"const MANIFEST = (\{.*?\});", text, re.S)
    assert match is not None
    manifest = json.loads(match.group(1))
    assert manifest["block"] == "alu8_func"
    assert len(manifest["nets"]) == 66
    assert "schematic" in manifest


def test_write_block_viewer_html(tmp_path: Path) -> None:
    manifest, svg = build_alu8_func_viewer_payload()
    path = write_block_viewer_html(manifest, svg, tmp_path / "alu8_func" / "index.html")
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "U_MUX4_0" in content
    assert "<svg" in content
