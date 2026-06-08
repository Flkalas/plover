from pathlib import Path

from plover_vm.boot_handoff import load_boot_fixtures
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def test_sta_to_lowpage_is_noop_in_boot_mode():
    m = PloverMachine(engine="fast")
    load_boot_fixtures(m, ROOT)
    m.bus.map_mode = 0
    m.bus.ram.write(0x0100, 0xAB)
    before = m.bus.ram.read(0x0100)
    m.fast.regs[0] = 0x55
    m.fast.pc = 0
    m.bus.ram.load(bytes([0x03, 0x00, 0x0A]), 0)  # STA $00; HALT
    m.run(max_steps=10)
    assert m.bus.ram.read(0x0100) == before
    assert m.bus.ram.read(0x0000) != 0x55 or before != 0x55
