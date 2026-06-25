"""Unit export bundle tests."""

import json
from pathlib import Path

from hwsim.units.export import export_units


def test_export_units_writes_gate_svgs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    nl_path = root / "hw/netlist/blocks/alu8.yaml"
    out = tmp_path / "units"
    manifest = export_units(nl_path, output_dir=out, html=True, embed_manifest=True)

    assert (out / "not_0.svg").is_file()
    assert (out / "alu8-gates.svg").is_file()
    assert (out / "alu8-gates.html").is_file()
    assert (out / "manifest.json").is_file()
    assert (out / "index.html").is_file()
    assert not (out / "alu8-full.svg").exists()
    assert len(manifest["units"]) == 34
    assert manifest.get("view") == "gate"

    svg = (out / "not_0.svg").read_text(encoding="utf-8")
    assert 'data-gate-view="1"' in svg
    assert 'id="gate"' in svg
    assert 'class="chip"' not in svg

    first = manifest["units"][0]
    assert first["svg"].endswith(".svg")
    assert "html" in first

    saved = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert saved["view"] == "gate"
    assert saved["graph_svg"] == "alu8-gates.svg"
