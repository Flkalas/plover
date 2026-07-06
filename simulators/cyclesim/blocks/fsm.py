"""CPLD idx5 FSM — phase counter and idx5 decode."""

from __future__ import annotations

from simulators.cyclesim.data.fsm_table import CtrlRow, FSM_BY_IDX5, idx5_index, lookup_row
from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H, L


class Idx5Decoder(Block):
    """Combinational DECODER: (opcode, phase) -> idx5 index."""

    def __init__(self, name: str = "idx5_dec") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        opc = sum((ctx.get(f"net_opc{i}") & 1) << i for i in range(5))
        ph = (ctx.get("net_ph0") & 1) | ((ctx.get("net_ph1") & 1) << 1)
        idx = idx5_index(opc, ph)
        changed = False
        for i in range(7):
            changed |= ctx.drive(f"net_idx{i}", (idx >> i) & 1, self.name)
        return changed


class PhaseCounter(Block):
    """2-bit phase counter — resets on macro_start."""

    def __init__(self, name: str = "phase") -> None:
        super().__init__(name)
        self.phase = 0

    def reset(self) -> None:
        self.phase = 0

    def advance(self) -> None:
        self.phase = (self.phase + 1) & 3

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        changed |= ctx.drive("net_ph0", self.phase & 1, self.name)
        changed |= ctx.drive("net_ph1", (self.phase >> 1) & 1, self.name)
        return changed


class CtrlLookup(Block):
    """Legacy monolithic control — merged strobes (pre dual-CPLD split)."""

    def __init__(self, name: str = "ctrl_lut") -> None:
        super().__init__(name)
        self.row: CtrlRow | None = None

    def load_opcode_phase(self, opcode: int, phase: int) -> CtrlRow | None:
        self.row = lookup_row(opcode, phase)
        return self.row

    def _drive_all_low(self, ctx: SimContext) -> bool:
        changed = False
        changed |= ctx.drive("net_reg_we", L, self.name)
        changed |= ctx.drive("net_mem_rd", L, self.name)
        changed |= ctx.drive("net_mem_wr", L, self.name)
        changed |= ctx.drive("net_y_oe", L, self.name)
        changed |= ctx.drive("net_w_sel0", L, self.name)
        changed |= ctx.drive("net_w_sel1", L, self.name)
        changed |= ctx.drive("net_cin", L, self.name)
        for i in range(4):
            changed |= ctx.drive(f"net_bctrl{i}", L, self.name)
            changed |= ctx.drive(f"net_lgc{i}", L, self.name)
        changed |= ctx.drive("net_153_s0", L, self.name)
        changed |= ctx.drive("net_153_s1", L, self.name)
        changed |= ctx.drive("net_pc_load_en", L, self.name)
        changed |= ctx.drive("net_pc_load_flg_z", L, self.name)
        changed |= ctx.drive("net_flg_we", L, self.name)
        return changed

    def eval_comb(self, ctx: SimContext) -> bool:
        if self.row is not None:
            r = self.row
            changed = False
            changed |= ctx.drive("net_reg_we", H if r.reg_we else L, self.name)
            changed |= ctx.drive("net_mem_rd", H if r.mem_rd else L, self.name)
            changed |= ctx.drive("net_mem_wr", H if r.mem_wr else L, self.name)
            changed |= ctx.drive("net_y_oe", H if r.y_oe else L, self.name)
            changed |= ctx.drive("net_w_sel0", r.w_sel & 1, self.name)
            changed |= ctx.drive("net_w_sel1", (r.w_sel >> 1) & 1, self.name)
            changed |= ctx.drive("net_cin", r.alu.cin, self.name)
            for i in range(4):
                changed |= ctx.drive(f"net_bctrl{i}", (r.alu.bctrl >> i) & 1, self.name)
                changed |= ctx.drive(f"net_lgc{i}", (r.alu.lgc >> i) & 1, self.name)
            changed |= ctx.drive("net_153_s0", r.alu.s0, self.name)
            changed |= ctx.drive("net_153_s1", r.alu.s1, self.name)
            changed |= ctx.drive("net_pc_load_en", H if r.pc_load_en else L, self.name)
            changed |= ctx.drive("net_pc_load_flg_z", H if r.pc_load_flg_z else L, self.name)
            changed |= ctx.drive("net_flg_we", H if r.flg_we else L, self.name)
            return changed

        return self._drive_all_low(ctx)


def row_for_idx5(idx: int) -> CtrlRow | None:
    return FSM_BY_IDX5.get(idx)
