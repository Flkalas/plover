"""VDU smoke YAML scenario gate."""

from pathlib import Path

import yaml

from plover_vm.vdu_scenario import run_vdu_scenario

ROOT = Path(__file__).resolve().parents[1]


def test_vdu_smoke_scenario():
    doc = yaml.safe_load((ROOT / "hw" / "scenarios" / "vm" / "vdu_smoke.yaml").read_text(encoding="utf-8"))
    res = run_vdu_scenario(doc, root=ROOT)
    assert res.error is None, res.error
    assert res.ok, res.output
