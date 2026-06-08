from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_vm.boot_handoff import load_boot_fixtures, simulate_sector_load
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_cmp_after_kernel_boot_sets_zero_flag():
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_boot_fixtures.py")], check=True)
    sector = bytes(assemble_file(ROOT / "hw" / "fixtures" / "sw" / "kernel_boot.asm").bytes).ljust(512, b"\x00")
    m = PloverMachine(engine="fast")
    load_boot_fixtures(m, ROOT)
    simulate_sector_load(m.bus, sector)
    m.bus.map_mode = 0
    m.reset(map_mode=0)
    m.run(max_steps=80_000)
    snap = m.snapshot()
    assert snap.flag_z is True
