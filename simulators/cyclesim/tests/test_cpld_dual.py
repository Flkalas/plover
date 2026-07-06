"""Dual CPLD (CU + DP) structural tests — rev G."""

from __future__ import annotations

import pytest

from simulators.cyclesim.blocks.cpld import (
    CpldCu,
    CpldDp,
    GicMerge,
    LutRom,
    TfrDetect,
    decode_g_ic,
)
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
from simulators.cyclesim.blocks.fetch import IrReg
from simulators.cyclesim.blocks.fsm import CtrlLookup, PhaseCounter, XferMux
from simulators.cyclesim.blocks.gpr import GprRegfile
from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr
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


def test_lut_add_ph1_w_sel_r1() -> None:
    ctx = SimContext()
    cu = CpldCu()
    ctx.add_block(cu)
    cu.load_opcode_phase(0x01, 1)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == H
    assert ctx.get(NET_W_SEL0_LUT) == H
    assert ctx.get(NET_W_SEL1_LUT) == L


@pytest.mark.parametrize(
    "opcode,src_reg,dst_reg",
    [
        (0x11, 1, 0),
        (0x12, 2, 0),
        (0x14, 0, 1),
        (0x16, 2, 1),
        (0x18, 0, 2),
        (0x19, 1, 2),
    ],
)
def test_tfr_gic_six_opcodes(opcode: int, src_reg: int, dst_reg: int) -> None:
    gic = decode_g_ic(opcode)
    assert opcode in TFR_OPS
    assert gic.tfr_valid
    assert gic.src == src_reg
    assert gic.w_sel == dst_reg
    assert decode_tfr(opcode) == (src_reg, dst_reg)

    ctx = SimContext()
    ir = IrReg()
    ir.ir = opcode
    phase = PhaseCounter()
    tfr = TfrDetect()
    ctx.add_block(ir)
    ctx.add_block(phase)
    ctx.add_block(tfr)
    phase.eval_comb(ctx)
    ir.eval_comb(ctx)
    tfr.eval_comb(ctx)
    ctx.comb_fixup()
    assert ctx.get(NET_GIC_TFR_VALID) == H
    src_net = (ctx.get(NET_GIC_SRC0) & 1) | ((ctx.get(NET_GIC_SRC1) & 1) << 1)
    assert src_net == src_reg
    w_sel = (ctx.get("net_tfr_w_sel0") & 1) | ((ctx.get("net_tfr_w_sel1") & 1) << 1)
    assert w_sel == dst_reg


def test_gic_merge_reg_we() -> None:
    ctx = SimContext()
    cu = CpldCu()
    ctx.add_block(cu)

    cu.load_opcode_phase(0x01, 1)
    _set_opcode(ctx, 0x01)
    _set_phase(ctx, 1)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == H
    assert ctx.get(NET_GIC_TFR_VALID) == L
    assert ctx.get(NET_GIC_REG_WE) == H

    cu.load_opcode_phase(0x11, 0)
    _set_opcode(ctx, 0x11)
    _set_phase(ctx, 0)
    _dual_fixup(ctx, cu)
    assert ctx.get(NET_REG_WE_LUT) == L
    assert ctx.get(NET_GIC_TFR_VALID) == H
    assert ctx.get(NET_GIC_REG_WE) == H


@pytest.mark.parametrize(
    "opcode,src_reg,dst_reg,value",
    [
        (0x11, 1, 0, 0xA1),
        (0x12, 2, 0, 0xA2),
        (0x14, 0, 1, 0xB0),
        (0x16, 2, 1, 0xB2),
        (0x18, 0, 2, 0xC0),
        (0x19, 1, 2, 0xC1),
    ],
)
def test_dp_tfr_all_pairs(opcode: int, src_reg: int, dst_reg: int, value: int) -> None:
    ctx = SimContext()
    dp = CpldDp()
    cu = CpldCu()
    for blk in (cu, dp):
        ctx.add_block(blk)

    dp.regs[src_reg] = value
    cu.load_opcode_phase(opcode, 0)
    _set_opcode(ctx, opcode)
    _set_phase(ctx, 0)
    _dual_fixup(ctx, cu)
    dp.apply_g_ic(ctx)

    if dst_reg == 0:
        assert dp.qa() == value
    elif dst_reg == 1:
        assert dp.qb() == value
    else:
        assert dp.read(2) == value


def _legacy_tfr(opcode: int, regs: list[int]) -> list[int]:
    ctx = SimContext()
    gpr = GprRegfile()
    gpr.regs = list(regs)
    ctrl = CtrlLookup()
    xfer = XferMux(gpr)
    xfer.opcode = opcode
    ctx.add_block(ctrl)
    ctx.add_block(gpr)
    ctx.add_block(xfer)
    ctrl.load_opcode_phase(opcode, 0)
    _set_opcode(ctx, opcode)
    _set_phase(ctx, 0)
    ctrl.eval_comb(ctx)
    xfer.eval_comb(ctx)
    ctx.comb_fixup()
    gpr.tick(ctx)
    return list(gpr.regs)


def _dual_tfr(opcode: int, regs: list[int]) -> list[int]:
    ctx = SimContext()
    dp = CpldDp()
    cu = CpldCu()
    for blk in (cu, dp):
        ctx.add_block(blk)
    dp.regs = list(regs)
    cu.load_opcode_phase(opcode, 0)
    _set_opcode(ctx, opcode)
    _set_phase(ctx, 0)
    _dual_fixup(ctx, cu)
    dp.apply_g_ic(ctx)
    return list(dp.regs)


@pytest.mark.parametrize("opcode", sorted(TFR_OPS))
def test_merged_equals_legacy_tfr(opcode: int) -> None:
    src, dst = decode_tfr(opcode)
    regs = [0x10, 0x20, 0x30]
    regs[src] = 0x55
    assert _dual_tfr(opcode, regs) == _legacy_tfr(opcode, regs)


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

    assert gpr.regs == dp.regs == [0x42, 0, 0]
    assert ctx_legacy.get("net_reg_we") == ctx_dual.get("net_reg_we") == H
    assert ctx_dual.get(NET_GIC_W_SEL0) == L
    assert ctx_dual.get(NET_GIC_W_SEL1) == L
