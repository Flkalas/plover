"""Macro instruction fetch + micro-phase delegation."""

from __future__ import annotations

from plover_vm.macro.isa import (
    OP_BEQ,
    OP_CALL,
    OP_HALT,
    OP_JMP,
    OP_MOV,
    OP_RET,
    OP_STA16,
    WIDE_ABS16_OPS,
    phase_count,
)
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
        self.rp = 0xF600
        self._ret_stack: list[int] = []

    def fetch_insn(self) -> None:
        fa = self.bus.fetch_addr(self.pc)
        op = self.bus.read_cpu(fa)
        if op in WIDE_ABS16_OPS:
            lo = self.bus.read_cpu((fa + 1) & 0xFFFF)
            hi = self.bus.read_cpu((fa + 2) & 0xFFFF)
            operand = lo | (hi << 8)
            insn_len = 3
        else:
            operand = self.bus.read_cpu((fa + 1) & 0xFFFF)
            insn_len = 2 if op != OP_RET and op != OP_HALT else 1
        self._current_op = op
        self._current_operand = operand
        op16 = operand if op in WIDE_ABS16_OPS else 0
        self.micro.reset_micro(
            op,
            operand & 0xFF,
            operand16=op16 if op == OP_STA16 else 0,
        )
        self.pc = (fa + insn_len) & 0xFFFF
        self._fetch_pending = False
        if op == OP_HALT:
            self.halted = True

    def _apply_macro_side_effects(self) -> None:
        op = self._current_op
        imm = self._current_operand
        if op == OP_BEQ and self.micro.state.flag_z:
            self.pc = imm & 0xFFFF
        elif op == OP_JMP:
            self.pc = imm & 0xFFFF
        elif op == OP_CALL:
            self._ret_stack.append(self.pc & 0xFFFF)
            self.pc = imm & 0xFFFF
        elif op == OP_RET:
            if self._ret_stack:
                self.pc = self._ret_stack.pop() & 0xFFFF
        elif op == OP_MOV:
            dst, src = (imm >> 4) & 3, imm & 3
            self.micro.state.regs[dst] = self.micro.state.regs[src] & 0xFF

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
            self._apply_macro_side_effects()
            self._fetch_pending = True
            self.micro.state.phase = 0

    @property
    def opcode(self) -> int:
        return self._current_op

    @property
    def operand(self) -> int:
        return self._current_operand
