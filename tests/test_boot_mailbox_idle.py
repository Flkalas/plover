from pathlib import Path

from plover_vm.boot_handoff import load_boot_fixtures, simulate_sector_load
from plover_vm.machine import PloverMachine
from plover_vm.memory.mailbox import CMD_NOP, MB_CMD, MB_STATUS, ST_READY

ROOT = Path(__file__).resolve().parents[1]


def test_mailbox_idle_after_boot_read_and_jmp():
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_boot_fixtures.py")], check=True)
    m = PloverMachine(engine="fast")
    load_boot_fixtures(m, ROOT)
    simulate_sector_load(m.bus, b"\x0A" + b"\x00" * 511)
    m.bus.map_mode = 0
    m.reset(map_mode=0)
    m.run(max_steps=80_000)
    assert m.bus.read_cpu(MB_STATUS) & ST_READY
    assert m.bus.read_cpu(MB_CMD) == CMD_NOP
    m.bus.write_cpu(MB_CMD, CMD_NOP)
    assert (m.bus.read_cpu(MB_STATUS) & ST_READY) or m.bus.read_cpu(MB_CMD) == CMD_NOP
