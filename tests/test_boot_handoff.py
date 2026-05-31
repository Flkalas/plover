from pathlib import Path

from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_boot_to_run_handoff():
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_boot_fixtures.py")], check=True)

    m = PloverMachine(engine="fast")
    m.load_nor(ROOT / "hw" / "fixtures" / "boot" / "boot_rom.hex", 0)
    m.load_nor(ROOT / "hw" / "fixtures" / "boot" / "boot_vector.hex", 0xFFFC)
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")

    m.bus.ram.write(0xFFFC, 0x00)
    m.bus.ram.write(0xFFFD, 0x08)
    m.bus.ram.write(0x0800, 0x0A)

    m.bus.map_mode = 1
    m.reset(map_mode=1)
    assert m.fast.pc == 0x0800
