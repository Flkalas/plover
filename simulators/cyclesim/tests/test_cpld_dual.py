"""Dual CPLD (CU + DP) structural tests — Gi1 v1.0."""

from __future__ import annotations

from simulators.cyclesim.blocks.cpld import CpldCu, CpldDp, GicMerge, LutRom
from simulators.cyclesim.blocks.cpld.gic import NET_GIC_REG_WE, NET_REG_WE_LUT
from simulators.cyclesim.blocks.fetch import IrReg
from simulators.cyclesim.blocks.fsm import CtrlLookup, PhaseCounter
from simulators.cyclesim.blocks.gpr import GprRegfile
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H, L


def _set_opcode(ctx: SimContext, opcode: int) -> None:
    for i in range(5):
        ctx.set(f"net_opc{i}", (opcode >> i) & 1)


def _set_phase(ctx: SimContext, phase: int) -> None:
    ctx.set("net_ph0", phase & 1)
    ctx.set("net_ph1", (phase >> 1) & 1)


def _dual_fixup(ctx: SimContext, cu: CpldCu) -> None:
    cu.eval_comb(ctx)
    ctx.flush_pending()


def test_lut_add_ph1_no_reg_we() -> None:
    """Gi1 ADD ph1: ALU only — no GPR write."""
    ctx = SimContext()
    cu = CpldCu()
    ctx.add_block(cu)
    cu.load_opcode_phase(0x01, 1)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == L


def test_gic_merge_reg_we() -> None:
    ctx = SimContext()
    cu = CpldCu()
    ctx.add_block(cu)

    cu.load_opcode_phase(0x02, 1)
    _set_opcode(ctx, 0x02)
    _set_phase(ctx, 1)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == H
    assert ctx.get(NET_GIC_REG_WE) == H

    cu.load_opcode_phase(0x01, 1)
    _set_opcode(ctx, 0x01)
    _set_phase(ctx, 1)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == L
    assert ctx.get(NET_GIC_REG_WE) == L


def test_dp_r0_lda_write() -> None:
    ctx = SimContext()
    dp = CpldDp()
    cu = CpldCu()
    for blk in (cu, dp):
        ctx.add_block(blk)

    cu.load_opcode_phase(0x02, 1)
    _set_opcode(ctx, 0x02)
    _set_phase(ctx, 1)
    _dual_fixup(ctx, cu)
    for i in range(8):
        ctx.set(f"net_d{i}", (0x42 >> i) & 1)
    ctx.comb_fixup()
    dp.apply_g_ic(ctx)
    assert dp.qa() == 0x42


def test_merged_equals_legacy_lda_ph1() -> None:
    ctx_legacy = SimContext()
    gpr = GprRegfile()
    ctrl = CtrlLookup()
    ctx_legacy.add_block(ctrl)
    ctx_legacy.add_block(gpr)
    ctrl.load_opcode_phase(0x02, 1)
    ctrl.eval_comb(ctx_legacy)
    for i in range(8):
        ctx_legacy.set(f"net_d{i}", (0x42 >> i) & 1)
    ctx_legacy.comb_fixup()
    gpr.tick(ctx_legacy)

    ctx_dual = SimContext()
    dp = CpldDp()
    cu = CpldCu()
    for blk in (cu, dp):
        ctx_dual.add_block(blk)
    cu.load_opcode_phase(0x02, 1)
    _set_opcode(ctx_dual, 0x02)
    _set_phase(ctx_dual, 1)
    _dual_fixup(ctx_dual, cu)
    for i in range(8):
        ctx_dual.set(f"net_d{i}", (0x42 >> i) & 1)
    ctx_dual.comb_fixup()
    dp.apply_g_ic(ctx_dual)

    assert gpr.regs[0] == dp.regs[0] == 0x42
    assert ctx_legacy.get("net_reg_we") == ctx_dual.get("net_reg_we") == H


def test_dp_mbr_to_alu_b() -> None:
    ctx = SimContext()
    dp = CpldDp()
    ctx.add_block(dp)
    dp.regs[0] = 0x10
    for i in range(8):
        ctx.set(f"net_mbr{i}", (0x05 >> i) & 1)
    dp.eval_comb(ctx)
    ctx.comb_fixup()
    b = sum((ctx.get(f"net_b{i}") & 1) << i for i in range(8))
    assert b == 0x05
    assert dp.qa() == 0x10
