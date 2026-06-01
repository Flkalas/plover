from pathlib import Path


def test_dos_boot_scenario():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    scen = root / "hw" / "scenarios" / "vm" / "dos_boot.yaml"
    subprocess.run([sys.executable, "-m", "plover_vm", "scenario", str(scen)], check=True)

