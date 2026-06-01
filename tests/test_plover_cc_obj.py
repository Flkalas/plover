from pathlib import Path
import subprocess
import sys

from plover_ld.format import read_plx

ROOT = Path(__file__).resolve().parents[1]


def test_plover_cc_object_emit(tmp_path: Path):
    src = ROOT / "hw" / "fixtures" / "sw" / "cc_smoke.c"
    out = tmp_path / "cc_smoke.plx"
    subprocess.run(
        [sys.executable, "-m", "plover_cc", str(src), "-c", "-o", str(out)],
        cwd=ROOT,
        check=True,
    )
    obj = read_plx(out)
    assert obj.name == "cc_smoke"
    assert len(obj.text) > 0
    assert any(s.name == "main" and s.section == "text" for s in obj.symbols)

