from __future__ import annotations

from pathlib import Path


def test_multi_drive_mount_copy_dir():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    img_b = root / "hw" / "fixtures" / "vfdd" / "test_multidrive_b.img"
    if img_b.exists():
        img_b.unlink()
    proc = subprocess.run(
        [sys.executable, "-m", "plover_vm", "dos-shell"],
        cwd=root,
        input=(
            "drives\n"
            "mount B test_multidrive_b.img\n"
            "drives\n"
            "copy A:README.TXT B:README.TXT\n"
            "dir B:\n"
            "B:\n"
            "dir\n"
            "unmount B\n"
            "exit\n"
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    out = proc.stdout
    assert "A>" in out
    assert "A: dos_boot.img *" in out or "A: dos_boot.img" in out
    assert "B: test_multidrive_b.img" in out
    assert "README" in out
    assert "ERR cannot unmount current" in out
    if img_b.exists():
        img_b.unlink()


def test_multi_drive_scenario():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    scen = root / "hw" / "scenarios" / "vm" / "dos_multidrive.yaml"
    img_b = root / "hw" / "fixtures" / "vfdd" / "dos_data.img"
    if img_b.exists():
        img_b.unlink()
    subprocess.run([sys.executable, "-m", "plover_vm", "scenario", str(scen)], check=True)
    if img_b.exists():
        img_b.unlink()
