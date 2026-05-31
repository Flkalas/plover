"""Macro instruction fetch + micro-phase delegation."""

from __future__ import annotations

from plover_vm.macro.isa import OP_HALT, phase_count
from plover_vm.memory.bus import MemoryBus
from plover_vm.micro.engine import MicroEngine


class MacroEngine:
    def __init__(self, bus: MemoryBus, micro: MicroEngine) -> None:
        self.bus = bus
        self.micro = micro
        self.pc = 0
        self.halted = False
        self._fetch_pending = True
        self._current_op = 0
        self._current_operand = 0

    def fetch_insn(self) -> None:
        fa = self.bus.fetch_addr(self.pc)
        op = self.bus.read_cpu(fa)
        operand = self.bus.read_cpu((fa + 1) & 0xFFFF)
        self._current_op = op
        self._current_operand = operand
        self.micro.reset_micro(op, operand)
        self.pc = (fa + 2) & 0xFFFF
        self._fetch_pending = False
        if op == OP_HALT:
            self.halted = True

    def step(self) -> None:
        if self.halted:
            return
        if self._fetch_pending:
            self.fetch_insn()
            if self.halted:
                return
        self.micro.step()
        n = phase_count(self._current_op)
        if self.micro.phases_done(n):
            self._fetch_pending = True
            self.micro.state.phase = 0

    @property
    def opcode(self) -> int:
        return self._current_op

    @property
    def operand(self) -> int:
        return self._current_operand
