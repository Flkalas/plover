"""CPLD-CU functional blocks — idx5 LUT, TFR detect, G-IC merge, branch."""

from __future__ import annotations

from simulators.cyclesim.blocks.cpld.gic import (
    NET_GIC_REG_WE,
    NET_GIC_SRC0,
    NET_GIC_SRC1,
    NET_GIC_TFR_VALID,
    NET_GIC_W_SEL0,
    NET_GIC_W_SEL1,
    NET_REG_WE_LUT,
    NET_W_SEL0_LUT,
    NET_W_SEL1_LUT,
)
from simulators.cyclesim.data.fsm_table import CtrlRow, lookup_row
from simulators.cyclesim.data.isa import decode_tfr, is_tfr_valid
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
        changed = False
        changed |= ctx.drive(NET_REG_WE_LUT, L, self.name)
        changed |= ctx.drive(NET_W_SEL0_LUT, L, self.name)
        changed |= ctx.drive(NET_W_SEL1_LUT, L, self.name)
        return changed

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
        changed |= ctx.drive(NET_W_SEL0_LUT, r.w_sel & 1, self.name)
        changed |= ctx.drive(NET_W_SEL1_LUT, (r.w_sel >> 1) & 1, self.name)
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


class TfrDetect(Block):
    """CU comb TFR — six opcodes → G-IC tfr_valid, src[1:0], w_sel[1:0]."""

    def __init__(self, name: str = "tfr_detect") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        op = sum((ctx.get(f"net_opc{i}") & 1) << i for i in range(5))
        ph = (ctx.get("net_ph0") & 1) | ((ctx.get("net_ph1") & 1) << 1)
        changed = False
        if is_tfr_valid(op) and ph == 0:
            src, dst = decode_tfr(op)
            changed |= ctx.drive(NET_GIC_TFR_VALID, H, self.name)
            changed |= ctx.drive(NET_GIC_SRC0, src & 1, self.name)
            changed |= ctx.drive(NET_GIC_SRC1, (src >> 1) & 1, self.name)
            changed |= ctx.drive("net_tfr_w_sel0", dst & 1, self.name)
            changed |= ctx.drive("net_tfr_w_sel1", (dst >> 1) & 1, self.name)
        else:
            changed |= ctx.drive(NET_GIC_TFR_VALID, L, self.name)
            changed |= ctx.drive(NET_GIC_SRC0, L, self.name)
            changed |= ctx.drive(NET_GIC_SRC1, L, self.name)
            changed |= ctx.drive("net_tfr_w_sel0", L, self.name)
            changed |= ctx.drive("net_tfr_w_sel1", L, self.name)
        return changed


class GicMerge(Block):
    """Merge LUT GPR strobes with TFR comb → G-IC bundle to DP."""

    def __init__(self, name: str = "gic_merge") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        tfr = ctx.get(NET_GIC_TFR_VALID) & 1
        reg_we_lut = ctx.get(NET_REG_WE_LUT) & 1
        reg_we = H if (reg_we_lut or tfr) else L
        if tfr:
            w0 = ctx.get("net_tfr_w_sel0") & 1
            w1 = ctx.get("net_tfr_w_sel1") & 1
        else:
            w0 = ctx.get(NET_W_SEL0_LUT) & 1
            w1 = ctx.get(NET_W_SEL1_LUT) & 1
        changed = False
        changed |= ctx.drive(NET_GIC_REG_WE, reg_we, self.name)
        changed |= ctx.drive(NET_GIC_W_SEL0, w0, self.name)
        changed |= ctx.drive(NET_GIC_W_SEL1, w1, self.name)
        # Merged SoC-visible aliases (bench / parity)
        changed |= ctx.drive("net_reg_we", reg_we, self.name)
        changed |= ctx.drive("net_w_sel0", w0, self.name)
        changed |= ctx.drive("net_w_sel1", w1, self.name)
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
    """CPLD-CU — LUT, TFR detect, G-IC merge (sequential eval within one comb pass)."""

    def __init__(self, name: str = "cpld_cu") -> None:
        super().__init__(name)
        self.lut = LutRom()
        self.tfr = TfrDetect()
        self.merge = GicMerge()

    def load_opcode_phase(self, opcode: int, phase: int) -> CtrlRow | None:
        return self.lut.load_opcode_phase(opcode, phase)

    @property
    def row(self) -> CtrlRow | None:
        return self.lut.row

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = self.lut.eval_comb(ctx)
        ctx.flush_pending()
        changed |= self.tfr.eval_comb(ctx)
        ctx.flush_pending()
        changed |= self.merge.eval_comb(ctx)
        return changed
