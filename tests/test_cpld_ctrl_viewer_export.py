"""CPLD control unit viewer export tests."""

import json
from pathlib import Path

from hwsim.units.export import export_units


def _export(root: Path, stem: str, out_name: str, min_units: int) -> Path:
    nl = root / f"hw/netlist/research/{stem}.yaml"
    cat = root / f"hw/units/research/{stem}.yaml"
    out = root / "build" / "test_exports" / out_name
    manifest = export_units(
        nl,
        output_dir=out,
        catalog_path=cat,
        html=True,
        embed_manifest=True,
        title=f"test {stem}",
    )
    assert (out / "index.html").is_file()
    assert (out / "manifest.json").is_file()
    assert (out / f"{stem}-gates.svg").is_file()
    saved = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert saved["view"] == "gate"
    assert len(saved["units"]) >= min_units
    assert manifest["block"] == stem
    return out


def test_export_counter_template_viewer(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = _export(root, "cpld_ctrl_counter", "counter_template", min_units=25)
    assert (out / "cpld_ctrl_counter-gates.html").is_file()
    assert (out / "phase_161.svg").is_file()


def test_export_flash_cw16_viewer(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = _export(root, "cpld_ctrl_cw16", "flash_cw16_direct", min_units=5)
    assert (out / "latch_stb.svg").is_file()
    assert (out / "latch_alu.svg").is_file()
