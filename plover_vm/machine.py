"""Plover v0.1 virtual machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plover_vm.loader import load_hex, load_sram_program
from plover_vm.macro.engine import MacroEngine
from plover_vm.macro.fast import MacroFastPath
from plover_vm.memory.bus import MemoryBus
from plover_vm.micro.cw import lookup_cw
from plover_vm.micro.engine import MicroEngine
from plover_vm.trace import Tracer

EngineKind = str  # "micro" | "macro" | "fast"


@dataclass
class MachineState:
    pc: int = 0
    regs: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    map_mode: int = 0
    halted: bool = False
    phase: int = 0
    opcode: int = 0


class PloverMachine:
    def __init__(self, engine: EngineKind = "micro") -> None:
        self.bus = MemoryBus()
        self.micro = MicroEngine(self.bus)
        self.macro = MacroEngine(self.bus, self.micro)
        self.fast = MacroFastPath(self.bus)
        self.engine = engine
        self.tracer = Tracer()
        self._steps = 0

    def load_nor(self, path: Path | str, offset: int = 0) -> None:
        self.bus.nor.load_hex(path, offset)

    def load_cw(self, path: Path | str) -> None:
        import sys

        root = Path(__file__).resolve().parents[1]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from tools.pack_control_store import CW_FLASH_BASE, build_all

        data, _ = load_hex(path, 0)
        if data:
            self.bus.nor.patch_cw_region(list(data), CW_FLASH_BASE)
        else:
            self.bus.nor.patch_cw_region(build_all(), CW_FLASH_BASE)

    def load_ram_program(self, path: Path | str, base: int = 0) -> None:
        prog = load_sram_program(path)
        self.bus.ram.load(prog, base)

    def load_ram_bytes(self, data: bytes | bytearray, base: int = 0) -> None:
        self.bus.ram.load(data, base)

    def set_map_mode(self, mode: int) -> None:
        self.bus.map_mode = mode & 1

    def reset(self, map_mode: int | None = None) -> None:
        if map_mode is not None:
            self.bus.map_mode = map_mode & 1
        fa = 0xFFFC
        lo = self.bus.read_cpu(fa)
        hi = self.bus.read_cpu((fa + 1) & 0xFFFF)
        entry = lo | (hi << 8)

        self.macro.pc = entry & 0xFFFF
        self.macro.halted = False
        self.macro._fetch_pending = True
        self.macro._ret_stack = []
        self.micro.state = self.micro.state.__class__()
        self.fast.pc = entry & 0xFFFF
        self.fast.halted = False
        self.fast.regs = [0, 0, 0, 0]
        self.fast._ret_stack = []
        self._steps = 0

    def step_once(self) -> None:
        if self.engine == "fast":
            self.fast.step()
            self._record_trace_fast()
            return

        self.macro.step()
        self._record_trace_micro()

    def _record_trace_micro(self) -> None:
        st = self.micro.state
        op = self.macro.opcode
        ph = max(0, st.phase - 1)
        cw = lookup_cw(self.bus.nor.read_cw, op, ph).raw if op else 0
        self.tracer.record(
            self.macro.pc,
            st.phase,
            op,
            cw,
            st.regs,
            self.macro.halted,
        )
        self._steps += 1

    def _record_trace_fast(self) -> None:
        self.tracer.record(
            self.fast.pc,
            0,
            0,
            0,
            self.fast.regs,
            self.fast.halted,
        )
        self._steps += 1

    def run(self, max_steps: int = 10_000) -> MachineState:
        for _ in range(max_steps):
            if self.halted:
                break
            self.step_once()
        return self.snapshot()

    @property
    def halted(self) -> bool:
        if self.engine == "fast":
            return self.fast.halted
        return self.macro.halted

    def snapshot(self) -> MachineState:
        if self.engine == "fast":
            return MachineState(
                pc=self.fast.pc,
                regs=list(self.fast.regs),
                map_mode=self.bus.map_mode,
                halted=self.fast.halted,
            )
        st = self.micro.state
        return MachineState(
            pc=self.macro.pc,
            regs=list(st.regs),
            map_mode=self.bus.map_mode,
            halted=self.macro.halted,
            phase=st.phase,
            opcode=self.macro.opcode,
        )

    @classmethod
    def from_config(
        cls,
        *,
        nor: Path | None = None,
        cw: Path | None = None,
        ram_prog: Path | None = None,
        map_mode: int = 0,
        engine: EngineKind = "micro",
    ) -> PloverMachine:
        m = cls(engine=engine)
        root = Path(__file__).resolve().parents[1]
        if nor:
            m.load_nor(nor)
        else:
            boot = root / "hw" / "fixtures" / "boot" / "boot_rom.hex"
            if boot.is_file():
                m.load_nor(boot, 0)
            vec = root / "hw" / "fixtures" / "boot" / "boot_vector.hex"
            if vec.is_file():
                m.load_nor(vec, 0xFFFC)
        if cw:
            m.load_cw(cw)
        else:
            cw_path = root / "hw" / "fixtures" / "control" / "cw.hex"
            if cw_path.is_file():
                m.load_cw(cw_path)
            else:
                m.load_cw(Path("/dev/null"))
        if ram_prog:
            m.load_ram_program(ram_prog, 0x0800 if map_mode else 0)
        m.bus.map_mode = map_mode
        return m
