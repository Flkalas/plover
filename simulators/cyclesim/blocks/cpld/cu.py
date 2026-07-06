"""CPLD-CU functional blocks — idx5 LUT, G-IC merge, branch (Gi1)."""

from __future__ import annotations

from simulators.cyclesim.blocks.cpld.gic import NET_GIC_REG_WE, NET_REG_WE_LUT
from simulators.cyclesim.data.fsm_table import CtrlRow, lookup_row
from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H, L


class LutRom(Block):
    """idx5 LUT — LUT-layer GPR strobes + 14 direct SoC strobes (CU)."""

    def __init__(self, name: str = "lut_rom") -> None:
        super().__init__(name)
        self.row: CtrlRow | None = None

    def load_opcode_phase(self, opcode: int, phase: int) -> CtrlRow | None:
        self.row = lookup_row(opcode, phase)
        return self.row

    def _drive_lut_low(self, ctx: SimContext) -> bool:
        return ctx.drive(NET_REG_WE_LUT, L, self.name)

    def _drive_soc_low(self, ctx: SimContext) -> bool:
        changed = False
        changed |= ctx.drive("net_mem_rd", L, self.name)
        changed |= ctx.drive("net_mem_wr", L, self.name)
        changed |= ctx.drive("net_y_oe", L, self.name)
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
        if self.row is None:
            changed = self._drive_lut_low(ctx)
            return changed | self._drive_soc_low(ctx)
        r = self.row
        changed = False
        changed |= ctx.drive(NET_REG_WE_LUT, H if r.reg_we else L, self.name)
        changed |= ctx.drive("net_mem_rd", H if r.mem_rd else L, self.name)
        changed |= ctx.drive("net_mem_wr", H if r.mem_wr else L, self.name)
        changed |= ctx.drive("net_y_oe", H if r.y_oe else L, self.name)
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


class GicMerge(Block):
    """LUT reg_we → G-IC (Gi1 — single wire)."""

    def __init__(self, name: str = "gic_merge") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        reg_we = H if (ctx.get(NET_REG_WE_LUT) & 1) else L
        changed = False
        changed |= ctx.drive(NET_GIC_REG_WE, reg_we, self.name)
        changed |= ctx.drive("net_reg_we", reg_we, self.name)
        return changed


class BranchAnd(Block):
    """BEQ: PC_LOAD gated by FLG_Z at macro_end (CPLD-CU)."""

    def __init__(self, name: str = "branch_and") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        if not (ctx.get("net_macro_end") & 1):
            return ctx.drive("net_pc_load", L, self.name)
        if not (ctx.get("net_pc_load_en") & 1):
            return ctx.drive("net_pc_load", L, self.name)
        if ctx.get("net_pc_load_flg_z") & 1:
            z = ctx.get("net_flg_z") & 1
            return ctx.drive("net_pc_load", H if z else L, self.name)
        return ctx.drive("net_pc_load", H, self.name)


class CpldCu(Block):
    """CPLD-CU — LUT + G-IC merge (Gi1)."""

    def __init__(self, name: str = "cpld_cu") -> None:
        super().__init__(name)
        self.lut = LutRom()
        self.merge = GicMerge()

    def load_opcode_phase(self, opcode: int, phase: int) -> CtrlRow | None:
        return self.lut.load_opcode_phase(opcode, phase)

    @property
    def row(self) -> CtrlRow | None:
        return self.lut.row

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = self.lut.eval_comb(ctx)
        ctx.flush_pending()
        changed |= self.merge.eval_comb(ctx)
        return changed
