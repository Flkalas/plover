"""Boot JMP handoff helpers (boot-jmp-handoff.md)."""

from __future__ import annotations

from pathlib import Path

from plover_vm.machine import PloverMachine
from plover_vm.memory.mailbox import CMD_READ, MB_CMD, MB_PARAM

SP_CELL = 0x0E00
RP_CELL = 0x0F00
SP_INIT = 0xE000
RP_INIT = 0xF600
KERNEL_ENTRY = 0x0800


def write_u16_le(bus, addr: int, val: int) -> None:
    bus.write_cpu(addr, val & 0xFF)
    bus.write_cpu(addr + 1, (val >> 8) & 0xFF)


def read_u16_le(bus, addr: int) -> int:
    lo = bus.read_cpu(addr)
    hi = bus.read_cpu(addr + 1)
    return lo | (hi << 8)


def simulate_sector_load(bus, image: bytes, *, base: int = KERNEL_ENTRY, sector: int = 0) -> None:
    """Prime mailbox sector stub (host-side READ model)."""
    bus.mailbox.set_sector_stub(image)
    bus.write_cpu(MB_PARAM, sector & 0xFF)
    bus.write_cpu(MB_CMD, CMD_READ)


def apply_boot_preinit(machine: PloverMachine) -> None:
    """Write SP/RP cells expected after Boot ROM boot_stacks (verification helper)."""
    write_u16_le(machine.bus, SP_CELL, SP_INIT)
    write_u16_le(machine.bus, RP_CELL, RP_INIT)
    if machine.engine == "fast":
        machine.fast.regs = [0, 0, 0, 0]
    else:
        machine.micro.state.regs = [0, 0, 0, 0]


def check_boot_preconditions(machine: PloverMachine) -> list[str]:
    """Return list of mismatch messages (empty if OK)."""
    errs: list[str] = []
    snap = machine.snapshot()
    if snap.regs != [0, 0, 0, 0]:
        errs.append(f"GPR expected [0,0,0,0] got {snap.regs}")
    sp = read_u16_le(machine.bus, SP_CELL)
    rp = read_u16_le(machine.bus, RP_CELL)
    if sp != SP_INIT:
        errs.append(f"SP cell expected 0x{SP_INIT:04X} got 0x{sp:04X}")
    if rp != RP_INIT:
        errs.append(f"RP cell expected 0x{RP_INIT:04X} got 0x{rp:04X}")
    return errs


def load_boot_fixtures(
    machine: PloverMachine,
    root: Path,
    *,
    nor_name: str = "boot_rom.hex",
    load_vector: bool = True,
) -> None:
    boot = root / "hw" / "fixtures" / "boot"
    machine.load_nor(boot / nor_name, 0)
    if load_vector:
        vec = boot / "boot_vector.hex"
        if vec.is_file():
            machine.load_nor(vec, 0xFFFC)
    machine.load_cw(root / "hw" / "fixtures" / "control" / "cw.hex")
