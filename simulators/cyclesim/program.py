"""Run machine programs on CpuM3b."""

from __future__ import annotations

from pathlib import Path

from simulators.cyclesim.cpu import CpuM3b


class ProgramRunner:
    def __init__(self, cpu: CpuM3b | None = None) -> None:
        self.cpu = cpu or CpuM3b()

    def load_rom_hex(self, path: str | Path, base: int = 0) -> None:
        self.cpu.mem.load_hex(str(path))

    def load_rom_bytes(self, blob: bytes, base: int = 0) -> None:
        self.cpu.mem.load_bytes(base, blob)

    def load_ram(self, addr: int, val: int) -> None:
        self.cpu.mem.write(addr, val)

    def reset(self, pc: int = 0) -> None:
        self.cpu.reset(pc)

    def run_until_halt(self, max_steps: int = 500) -> int:
        return self.cpu.run(max_steps)

    @property
    def gpr(self) -> list[int]:
        return list(self.cpu.gpr.regs)

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
