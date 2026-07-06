"""M3b CPU — dual CPLD idx5 FSM + ALU + net-faithful fetch/execute."""

from __future__ import annotations

from simulators.cyclesim.blocks.alu8_block import Alu8Block
from simulators.cyclesim.blocks.cpld import BranchAnd, CpldCu, CpldDp
from simulators.cyclesim.blocks.fetch import (
    Abs16HiReg,
    AddrMux,
    FlgReg,
    IrReg,
    MbrReg,
    MemArray,
    PcInMux,
    PcReg,
    YBusMux,
)
from simulators.cyclesim.blocks.fsm import Idx5Decoder, PhaseCounter
from simulators.cyclesim.data.fsm_table import Template
from simulators.cyclesim.data.isa import (
    OP_HALT,
    OP_LDIO,
    OP_STA16,
    OP_STIO,
    insn_length,
    phase_count,
)
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H, L


class CpuM3b:
    """Functional-block CPU for M3b fetch + execute (rev G dual CPLD)."""

    def __init__(self) -> None:
        self.ctx = SimContext()
        self.cpld_dp = CpldDp()
        self.pc = PcReg()
        self.ir = IrReg()
        self.mbr = MbrReg()
        self.abs16_hi = Abs16HiReg()
        self.flg = FlgReg()
        self.mem = MemArray()
        self.phase = PhaseCounter()
        self.cpld_cu = CpldCu()
        self.alu_blk = Alu8Block()
        self.addr_mux = AddrMux()
        self.pc_in_mux = PcInMux()
        self.y_bus = YBusMux()
        self.branch = BranchAnd()

        for blk in (
            self.pc,
            self.ir,
            self.mbr,
            self.abs16_hi,
            self.flg,
            self.mem,
            self.addr_mux,
            self.pc_in_mux,
            self.cpld_dp,
            self.phase,
            self.cpld_cu,
            Idx5Decoder(),
            self.y_bus,
            self.alu_blk,
            self.branch,
        ):
            self.ctx.add_block(blk)

        self.halted = False
        self.fetch_pending = True
        self._fetch_byte = 0
        self._fetch_ilen = 0
        self.current_op = 0
        self._bus_data = 0

        self._trace_fetch: dict[str, int | bool] = {}

    @property
    def gpr(self) -> CpldDp:
        """GPR datapath alias (CPLD-DP)."""
        return self.cpld_dp

    def reset(self, pc: int | None = None, *, from_vector: bool = False) -> None:
        if from_vector or pc is None:
            if self.mem.sys.rom.get(0xFFFC) is not None or self.mem.sys.rom.get(0xFFFD) is not None:
                pc = self.mem.sys.reset_vector()
            else:
                pc = 0
        self.pc.pc = pc & 0xFFFF
        self.phase.reset()
        self.halted = False
        self.fetch_pending = True
        self._fetch_byte = 0
        self._fetch_ilen = 0
        self.current_op = 0
        self.cpld_dp.regs = [0, 0, 0]
        self.flg.z = False
        self.flg.c = False
        self.ir.ir = 0
        self.mbr.mbr = 0
        self.abs16_hi.hi = 0

    def _default_nets(self) -> None:
        for net in (
            "net_fetch",
            "net_mem_rd",
            "net_mem_wr",
            "net_reg_we",
            "net_y_oe",
            "net_y_src_a",
            "net_ir_load",
            "net_mbr_load",
            "net_abs16_hi_load",
            "net_pc_load",
            "net_pc_inc",
            "net_flg_we",
            "net_macro_end",
            "net_ldio_stio",
            "net_abs16_addr",
        ):
            self.ctx.set(net, L)

    def _sync_phase_nets(self) -> None:
        self.phase.eval_comb(self.ctx)

    def _sync_opcode_nets(self) -> None:
        self.ir.eval_comb(self.ctx)

    def _latch_mem_d_for_fetch(self) -> None:
        """Hold mem_d stable through IR/MBR clock — comb fixpoint can glitch addr during tick."""
        addr = self.pc.pc & 0xFFFF
        val = self.mem.read(addr)
        for i in range(8):
            self.ctx.set(f"net_mem_d{i}", (val >> i) & 1, stuck=True)

    def _fetch_tick(self) -> None:
        self.ctx.clear_stuck()
        self._default_nets()
        self.ctx.set("net_fetch", H)
        self._sync_phase_nets()
        self.ctx.comb_fixup()

        if self._fetch_byte == 0:
            self._trace_fetch = {"net_fetch": H, "pc_inc_count": 0}
            self.ctx.set("net_ir_load", H)
            self._latch_mem_d_for_fetch()
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["net_ir_load"] = True
            self.ctx.set("net_ir_load", L)

            op = self.ir.ir
            if op == OP_HALT:
                self.halted = True
                self.fetch_pending = False
                return

            self.ctx.set("net_pc_inc", H)
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["pc_inc_count"] = 1

            self._fetch_ilen = insn_length(op)
            self.current_op = op
            if self._fetch_ilen == 1:
                self._finish_fetch()
            else:
                self._fetch_byte = 1
            return

        if self._fetch_byte == 1:
            self._trace_fetch = {"net_fetch": H, "pc_inc_count": 0}
            self.ctx.set("net_mbr_load", H)
            self._latch_mem_d_for_fetch()
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["net_mbr_load"] = True
            self.ctx.set("net_mbr_load", L)

            self.ctx.set("net_pc_inc", H)
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["pc_inc_count"] = self._trace_fetch.get("pc_inc_count", 0) + 1

            if self._fetch_ilen == 2:
                self._finish_fetch()
            else:
                self._fetch_byte = 2
            return

        if self._fetch_byte == 2:
            self._trace_fetch = {"net_fetch": H, "pc_inc_count": 0}
            self.ctx.set("net_abs16_hi_load", H)
            self._latch_mem_d_for_fetch()
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["net_abs16_hi_load"] = True
            self.ctx.set("net_abs16_hi_load", L)

            self.ctx.set("net_pc_inc", H)
            self.ctx.comb_fixup()
            self.ctx.pulse_clock()
            self._trace_fetch["pc_inc_count"] = self._trace_fetch.get("pc_inc_count", 0) + 1
            self._finish_fetch()

    def _finish_fetch(self) -> None:
        self.phase.reset()
        self._sync_phase_nets()
        self.fetch_pending = False
        self._fetch_byte = 0
        self._fetch_ilen = 0

    def _drive_d_from_qa(self) -> None:
        val = self.cpld_dp.qa()
        for i in range(8):
            self.ctx.set(f"net_d{i}", (val >> i) & 1, stuck=True)

    def _drive_d_from_mbr(self) -> None:
        val = self.mbr.mbr
        for i in range(8):
            self.ctx.set(f"net_d{i}", (val >> i) & 1, stuck=True)

    def _drive_d_from_bus(self) -> None:
        val = self._bus_data
        for i in range(8):
            self.ctx.set(f"net_d{i}", (val >> i) & 1, stuck=True)

    def _eff_addr(self, op: int) -> int:
        from simulators.cyclesim.blocks.mem_decode import MAILBOX_BASE

        if op in (OP_LDIO, OP_STIO):
            return MAILBOX_BASE | (self.mbr.mbr & 0xFF)
        if op == OP_STA16:
            return (self.mbr.mbr & 0xFF) | ((self.abs16_hi.hi & 0xFF) << 8)
        return self.mbr.mbr & 0xFFFF

    def execute_phase(self) -> None:
        op = self.current_op
        ph = self.phase.phase
        row = self.cpld_cu.load_opcode_phase(op, ph)
        self.ctx.clear_stuck()
        self._default_nets()
        self._sync_phase_nets()
        self._sync_opcode_nets()

        if row and row.template == Template.MEM_LD and row.mem_rd:
            if op in (OP_LDIO, OP_STIO):
                self.ctx.set("net_ldio_stio", H, stuck=True)
            self.ctx.set("net_mem_rd", H, stuck=True)
        if row and row.template == Template.MEM_ST and row.mem_wr:
            if op in (OP_LDIO, OP_STIO):
                self.ctx.set("net_ldio_stio", H, stuck=True)
            elif op == OP_STA16:
                self.ctx.set("net_abs16_addr", H, stuck=True)
            self.ctx.set("net_mem_wr", H, stuck=True)
            self._drive_d_from_qa()
        if row and row.template == Template.MEM_ST and row.y_oe:
            self.ctx.set("net_y_src_a", H, stuck=True)

        self.ctx.comb_fixup()

        if row and row.template == Template.MEM_LD and row.mem_rd:
            self._bus_data = self.mem.read(self._eff_addr(op))
        if row and row.template == Template.MEM_ST and row.mem_wr:
            self.mem.write(self._eff_addr(op), self.cpld_dp.qa())
        if row and row.reg_we:
            if row.template == Template.ALU_REG and ph == 1 and row.w_sel == 1:
                self._drive_d_from_mbr()
            elif row.template == Template.MEM_LD:
                self._drive_d_from_bus()

        self.ctx.comb_fixup()
        self.ctx.pulse_clock()
        self.phase.advance()

    def _macro_end_tick(self) -> None:
        op = self.current_op
        n = phase_count(op)
        last_ph = max(0, n - 1)
        self.cpld_cu.load_opcode_phase(op, last_ph)
        self.ctx.clear_stuck()
        self._default_nets()
        self._sync_phase_nets()
        self._sync_opcode_nets()
        self.ctx.comb_fixup()
        self.ctx.set("net_macro_end", H)
        self.ctx.comb_fixup()
        self.ctx.pulse_clock()
        self.ctx.set("net_macro_end", L)

    def step(self) -> None:
        if self.halted:
            return
        if self.fetch_pending:
            self._fetch_tick()
            return

        n = phase_count(self.current_op)
        if self.phase.phase >= n:
            self._macro_end_tick()
            self.fetch_pending = True
            self.phase.reset()
            return

        self.execute_phase()

        if self.phase.phase >= n:
            self._macro_end_tick()
            self.fetch_pending = True
            self.phase.reset()

    def run(self, max_steps: int = 500, *, wall_s: float = 10.0) -> int:
        import time

        deadline = time.monotonic() + wall_s
        steps = 0
        while not self.halted and steps < max_steps:
            if time.monotonic() > deadline:
                break
            self.step()
            steps += 1
        return steps

    @property
    def current_operand(self) -> int:
        return self.mbr.mbr & 0xFF

    @property
    def current_operand16(self) -> int:
        return (self.mbr.mbr & 0xFF) | ((self.abs16_hi.hi & 0xFF) << 8)

    @property
    def operand16(self) -> int:
        return self.current_operand16
