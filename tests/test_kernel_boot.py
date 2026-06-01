from pathlib import Path


def test_os_boot_scenario():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    scen = root / "hw" / "scenarios" / "vm" / "os_boot.yaml"
    subprocess.run([sys.executable, "-m", "plover_vm", "scenario", str(scen)], check=True)

