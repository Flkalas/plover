"""Direct ISA semantics without micro-phases."""

from __future__ import annotations

from plover_vm.alu import alu8
from plover_vm.alu16 import add16, cmp16_u
from plover_vm.micro.normative import apply_add, apply_beq_compare, apply_cmp_flags
from plover_vm.macro.isa import (
    OP_ADD,
    OP_ADD_RR,
    OP_BCS,
    OP_BEQ,
    OP_CALL,
    OP_CMP,
    OP_HALT,
    OP_JMP,
    OP_LDA,
    OP_LDIO,
    OP_MOV,
    OP_RET,
    OP_STA,
    OP_STA16,
    OP_STIO,
    OP_WADD_RR,
    OP_WCMP16,
    OP_WMOV,
    WIDE_ABS16_OPS,
    WIDE_IMM16_OPS,
)
from plover_vm.macro.mmio import mmio_addr
from plover_vm.memory.bus import MemoryBus


class MacroFastPath:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus
        self.pc = 0
        self.regs = [0, 0, 0, 0]
        self.regs16 = [0, 0, 0, 0]
        self.flag_z = False
        self.flag_c = False
        self.halted = False
        self._ret_stack: list[int] = []

    def _read_byte(self, addr: int) -> int:
        return self.bus.read_cpu(addr) & 0xFF

    def fetch_decode_execute(self) -> None:
        if self.halted:
            return
        fa = self.bus.fetch_addr(self.pc)
        op = self._read_byte(fa)

        if op in WIDE_IMM16_OPS:
            imm16 = self._read_byte(fa + 1) | (self._read_byte(fa + 2) << 8)
            self.pc = (fa + 3) & 0xFFFF
            imm = imm16
        elif op in WIDE_ABS16_OPS:
            imm = self._read_byte(fa + 1) | (self._read_byte(fa + 2) << 8)
            self.pc = (fa + 3) & 0xFFFF
        elif op in (OP_RET, OP_HALT, OP_ADD_RR):
            imm = 0
            self.pc = (fa + 1) & 0xFFFF
        else:
            imm = self._read_byte(fa + 1)
            self.pc = (fa + 2) & 0xFFFF

        if op == OP_HALT:
            self.halted = True
        elif op == OP_ADD:
            self.regs, self.flag_z, self.flag_c = apply_add(self.regs, imm)
        elif op == OP_ADD_RR:
            r = alu8(self.regs[0], self.regs[1], 1)
            self.regs[2] = r.y
            self.flag_z = r.zero
            self.flag_c = r.cout
        elif op == OP_MOV:
            dst, src = (imm >> 4) & 3, imm & 3
            self.regs[dst] = self.regs[src] & 0xFF
        elif op == OP_CMP:
            self.flag_z, self.flag_c = apply_cmp_flags(self.regs, imm)
        elif op == OP_WADD_RR:
            r = add16(self.regs16[0], self.regs16[1])
            self.regs16[2] = r.y
            self.flag_z = r.zero
            self.flag_c = r.cout
        elif op == OP_WMOV:
            dst, src = (imm >> 4) & 3, imm & 3
            self.regs16[dst] = self.regs16[src] & 0xFFFF
        elif op == OP_WCMP16:
            r = cmp16_u(self.regs16[0], imm)
            self.flag_z = r.zero
            self.flag_c = r.cout
        elif op == OP_BCS:
            if self.flag_c:
                self.pc = imm & 0xFFFF
        elif op == OP_LDA:
            self.regs[0] = self._read_byte(imm)
        elif op == OP_STA:
            self.bus.write_cpu(imm, self.regs[0])
        elif op == OP_STA16:
            self.bus.write_cpu(imm, self.regs[0])
        elif op == OP_BEQ:
            self.flag_z, self.flag_c = apply_beq_compare(self.regs, imm)
            if self.flag_z:
                self.pc = imm & 0xFFFF
        elif op == OP_JMP:
            self.pc = imm & 0xFFFF
        elif op == OP_CALL:
            self._ret_stack.append(self.pc & 0xFFFF)
            self.pc = imm & 0xFFFF
        elif op == OP_RET:
            if self._ret_stack:
                self.pc = self._ret_stack.pop() & 0xFFFF
        elif op == OP_LDIO:
            self.regs[0] = self._read_byte(mmio_addr(imm))
        elif op == OP_STIO:
            self.bus.write_cpu(mmio_addr(imm), self.regs[0])

    def step(self) -> None:
        self.fetch_decode_execute()

    def sync_from_micro(self, regs: list[int], flag_z: bool, pc: int) -> None:
        self.regs = list(regs)
        self.flag_z = flag_z
        self.pc = pc
