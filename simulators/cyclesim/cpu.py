"""M3b CPU — CPLD idx5 FSM + ALU + fetch path."""

from __future__ import annotations

from simulators.cyclesim.blocks.alu8_block import Alu8Block
from simulators.cyclesim.blocks.fetch import AddrMux, FlgReg, IrReg, MbrReg, MemArray, PcReg
from simulators.cyclesim.blocks.fsm import BranchAnd, CtrlLookup, PhaseCounter, XferMux
from simulators.cyclesim.blocks.gpr import GprRegfile
from simulators.cyclesim.data.fsm_table import Template
from simulators.cyclesim.data.isa import (
    OP_BEQ,
    OP_HALT,
    OP_JMP,
    decode_tfr,
    insn_length,
    is_tfr_valid,
    phase_count,
)
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H, L


class CpuM3b:
    """Functional-block CPU for M3b fetch + execute."""

    def __init__(self) -> None:
        self.ctx = SimContext()
        self.gpr = GprRegfile()
        self.pc = PcReg()
        self.ir = IrReg()
        self.mbr = MbrReg()
        self.flg = FlgReg()
        self.mem = MemArray()
        self.phase = PhaseCounter()
        self.ctrl = CtrlLookup()
        self.xfer = XferMux(self.gpr)
        self.alu_blk = Alu8Block()
        self._bus_data = 0

        for blk in (
            self.pc,
            self.ir,
            self.mbr,
            self.flg,
            self.mem,
            AddrMux(),
            self.gpr,
            self.phase,
            self.ctrl,
            self.xfer,
            BranchAnd(),
            self.alu_blk,
        ):
            self.ctx.add_block(blk)

        self.halted = False
        self.fetch_pending = True
        self.current_op = 0
        self.current_operand = 0
        self.current_operand16 = 0

    def reset(self, pc: int = 0) -> None:
        self.pc.pc = pc & 0xFFFF
        self.phase.reset()
        self.halted = False
        self.fetch_pending = True
        self.gpr.regs = [0, 0, 0]
        self.flg.z = False
        self.flg.c = False
        self._bus_data = 0

    def fetch_insn(self) -> None:
        if self.halted:
            return
        fa = self.pc.pc
        op = self.mem.read(fa)
        if op == OP_HALT:
            self.halted = True
            self.fetch_pending = False
            return

        ilen = insn_length(op)
        operand = 0
        operand16 = 0
        if ilen == 3:
            lo = self.mem.read((fa + 1) & 0xFFFF)
            hi = self.mem.read((fa + 2) & 0xFFFF)
            operand16 = lo | (hi << 8)
            operand = lo
        elif ilen == 2:
            operand = self.mem.read((fa + 1) & 0xFFFF)

        self.ir.ir = op
        self.mbr.mbr = operand & 0xFF
        self.current_op = op
        self.current_operand = operand & 0xFF
        self.current_operand16 = operand16 & 0xFFFF
        self.pc.pc = (fa + ilen) & 0xFFFF
        self.phase.reset()
        self.fetch_pending = False
        self.xfer.opcode = op

    def _drive_d_bus(self, val: int) -> None:
        for i in range(8):
            self.ctx.set(f"net_d{i}", (val >> i) & 1, stuck=True)

    def execute_phase(self) -> None:
        op = self.current_op
        ph = self.phase.phase
        row = self.ctrl.load_opcode_phase(op, ph)
        self.ctx.clear_stuck()

        self.ctx.set("net_fetch", L)
        self.ctx.set("net_mem_rd", L)
        self.ctx.set("net_mem_wr", L)
        self.ctx.set("net_reg_we", L)
        self.ctx.set("net_y_oe", L)
        self.ctx.set("net_ir_load", L)
        self.ctx.set("net_mbr_load", L)
        self.ctx.set("net_pc_load", L)
        self.ctx.set("net_pc_inc", L)
        self.ctx.set("net_flg_we", L)

        if row and row.template == Template.MEM_LD and row.mem_rd:
            self.ctx.set("net_mem_rd", H)
        if row and row.template == Template.MEM_ST and row.mem_wr:
            self.ctx.set("net_mem_wr", H)

        self.ctx.comb_fixup()

        if row and row.template == Template.MEM_LD and row.mem_rd:
            self._bus_data = self.mem.read(self.mbr.mbr) & 0xFF

        if row and row.reg_we:
            if row.template == Template.ALU_REG and ph == 1 and row.w_sel == 1:
                self._drive_d_bus(self.mbr.mbr)
            elif row.template == Template.MEM_LD:
                self._drive_d_bus(self._bus_data)
            elif row.template == Template.ALU_REG and ph == 2:
                self.ctx.comb_fixup()
        elif is_tfr_valid(op) and ph == 0:
            self.ctx.set("net_reg_we", H)
            _src, dst = decode_tfr(op)
            self.ctx.set("net_w_sel0", dst & 1)
            self.ctx.set("net_w_sel1", (dst >> 1) & 1)
            self.ctx.comb_fixup()

        self.ctx.pulse_clock()

        self.phase.advance()

    def macro_end(self) -> None:
        op = self.current_op
        if op == OP_BEQ and self.flg.z:
            self.pc.pc = self.current_operand16 & 0xFFFF
        elif op == OP_JMP:
            self.pc.pc = self.current_operand16 & 0xFFFF

    def step(self) -> None:
        if self.halted:
            return
        if self.fetch_pending:
            self.fetch_insn()
            return

        n = phase_count(self.current_op)
        if self.phase.phase >= n:
            self.macro_end()
            self.fetch_pending = True
            self.phase.reset()
            return

        self.execute_phase()

        if self.phase.phase >= n:
            self.macro_end()
            self.fetch_pending = True
            self.phase.reset()

    def run(self, max_steps: int = 500) -> int:
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
        return steps
