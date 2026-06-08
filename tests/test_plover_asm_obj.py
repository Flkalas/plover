from pathlib import Path
import subprocess
import sys

from plover_ld.format import read_plx

ROOT = Path(__file__).resolve().parents[1]


def test_plover_asm_object_emit(tmp_path: Path):
    src = ROOT / "hw" / "fixtures" / "sw" / "add_imm.asm"
    out_dir = tmp_path / "obj"
    subprocess.run(
        [sys.executable, "-m", "plover_asm", "obj", str(src), "-o", str(out_dir)],
        cwd=ROOT,
        check=True,
    )
    obj = read_plx(out_dir / "add_imm.plx")
    assert obj.name == "add_imm"
    assert len(obj.text) == 9

