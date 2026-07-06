"""Run machine programs on CpuM3b."""

from __future__ import annotations

from pathlib import Path

from simulators.cyclesim.cpu import CpuM3b


class ProgramRunner:
    def __init__(self, cpu: CpuM3b | None = None) -> None:
        self.cpu = cpu or CpuM3b()

    def load_rom_hex(self, path: str | Path, base: int = 0) -> None:
        self.cpu.mem.load_hex(str(path), target="rom")
        self.cpu.mem.load_hex(str(path), target="ram")

    def load_rom_bytes(self, blob: bytes, base: int = 0) -> None:
        self.cpu.mem.load_bytes(base, blob, target="rom")
        self.cpu.mem.load_bytes(base, blob, target="ram")

    def load_ram(self, addr: int, val: int) -> None:
        self.cpu.mem.load_ram(addr, val)

    def reset(self, pc: int | None = None, *, from_vector: bool = False, map_mode: int = 1) -> None:
        self.cpu.mem.map_mode = map_mode
        self.cpu.reset(pc, from_vector=from_vector)

    def run_until_halt(self, max_steps: int = 500, *, wall_s: float = 10.0) -> int:
        return self.cpu.run(max_steps, wall_s=wall_s)

    @property
    def r0(self) -> int:
        return self.cpu.gpr.regs[0] & 0xFF

    @property
    def gpr(self) -> list[int]:
        return [self.r0]

    @property
    def halted(self) -> bool:
        return self.cpu.halted

    @property
    def pc(self) -> int:
        return self.cpu.pc.pc

    @property
    def ir(self) -> int:
        return self.cpu.ir.ir

    @property
    def mbr(self) -> int:
        return self.cpu.mbr.mbr
