from pathlib import Path

from plover_vm.boot_handoff import load_boot_fixtures
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_reset_returns_to_rom_vector_boot_mode():
    m = PloverMachine(engine="fast")
    load_boot_fixtures(m, ROOT)
    m.bus.map_mode = 0
    m.reset(map_mode=0)
    assert m.fast.pc == 0x0000
    m.fast.pc = 0x0900
    m.fast.regs = [1, 2, 3, 4]
    m.reset(map_mode=0)
    assert m.fast.pc == 0x0000
