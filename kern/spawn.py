"""Spawn/EXEC loader for PL-DOS (S7c)."""

from __future__ import annotations

from dataclasses import dataclass

from kern.plfs import Plfs
from kern.plr import unpack_plr
from plover_vm.machine import PloverMachine


@dataclass(frozen=True)
class ExecResult:
    halted: bool
    r0: int


def spawn(machine: PloverMachine, fs: Plfs, name: str, *, engine: str = "micro") -> ExecResult:
    plr = unpack_plr(fs.read(name))
    machine.engine = engine
    machine.load_ram_bytes(plr.code, plr.load_addr)
    machine.bus.map_mode = 1
    if engine == "fast":
        machine.fast.pc = plr.entry_addr
        machine.fast.halted = False
        machine.run(max_steps=10_000)
        return ExecResult(halted=machine.fast.halted, r0=machine.fast.regs[0] & 0xFF)
    machine.macro.pc = plr.entry_addr
    machine.macro.halted = False
    machine.macro._fetch_pending = True
    machine.run(max_steps=50_000)
    return ExecResult(halted=machine.macro.halted, r0=machine.micro.state.regs[0] & 0xFF)

