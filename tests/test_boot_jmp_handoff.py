from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_vm.boot_handoff import (
    KERNEL_ENTRY,
    check_boot_preconditions,
    load_boot_fixtures,
    simulate_sector_load,
)
from plover_vm.machine import PloverMachine

ROOT = Path(__file__).resolve().parents[1]


def _kernel_sector() -> bytes:
    img = bytes(assemble_file(ROOT / "hw" / "fixtures" / "sw" / "kernel_boot.asm").bytes)
    return img.ljust(512, b"\x00")


def _machine(engine: str = "fast") -> PloverMachine:
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_boot_fixtures.py")], check=True)
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "pack_control_store.py"), "--build-fixtures"],
        check=True,
    )
    m = PloverMachine(engine=engine)
    load_boot_fixtures(m, ROOT, nor_name="boot_rom.hex")
    simulate_sector_load(m.bus, _kernel_sector())
    m.bus.map_mode = 0
    m.reset(map_mode=0)
    return m


def test_jmp_handoff_reaches_kernel():
    m = _machine("fast")
    m.run(max_steps=80_000)
    snap = m.snapshot()
    assert snap.map_mode == 0
    assert snap.halted
    assert snap.pc in (0x0805, 0x0806)
    assert check_boot_preconditions(m) == []


def test_jmp_handoff_micro_engine():
    m = _machine("micro")
    m.run(max_steps=200_000)
    snap = m.snapshot()
    assert snap.halted
    assert snap.pc in (0x0805, 0x0806)


def test_jmp_handoff_sp_rp_cells():
    m = _machine("fast")
    m.run(max_steps=80_000)
    from plover_vm.boot_handoff import read_u16_le, RP_CELL, RP_INIT, SP_CELL, SP_INIT

    assert read_u16_le(m.bus, SP_CELL) == SP_INIT
    assert read_u16_le(m.bus, RP_CELL) == RP_INIT


def test_kernel_ram_entry():
    m = _machine("fast")
    m.run(max_steps=80_000)
    assert m.bus.read_cpu(KERNEL_ENTRY) == 0x0D
