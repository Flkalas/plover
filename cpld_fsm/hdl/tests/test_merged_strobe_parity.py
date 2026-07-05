"""LUT → PLD merge → cyclesim CtrlLookup merged strobe parity."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HDL = Path(__file__).resolve().parents[1]
REPO = HDL.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(HDL) not in sys.path:
    sys.path.insert(0, str(HDL))

from fsm_golden import (
    CYCLESIM_NET_MAP,
    FSM_OUTPUT_SIGNALS,
    cyclesim_bools,
    merged_bools,
    pc_load_at_macro_end,
    row_bools,
    sim_env,
)
from sim_fsm_eval import eval_ctrl_lut_signal, load_ctrl_lut_equations
from simulators.cyclesim.blocks.fsm import BranchAnd, CtrlLookup
from simulators.cyclesim.data.fsm_table import FSM_ROWS
from simulators.cyclesim.data.isa import OP_BEQ, OP_JMP, TFR_OPS
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H, L

LUT = HDL / "ctrl_lut.inc"

MERGE_PIN_SIGNALS = tuple(k for k in CYCLESIM_NET_MAP if k != "lut_pc_load" and k != "lut_pc_flg_z")


@pytest.fixture(scope="module")
def lut_equations() -> dict[str, str]:
    if not LUT.is_file():
        pytest.skip(f"missing {LUT.name} — run gen_ctrl_lut.py first")
    return load_ctrl_lut_equations(LUT)


def _lut_from_eval(row, lut_equations: dict[str, str]) -> dict[str, bool]:
    return {
        sig: eval_ctrl_lut_signal(lut_equations, sig, row.opcode, row.phase)
        for sig in FSM_OUTPUT_SIGNALS
    }


def _drive_cyclesim(ctx: SimContext, opcode: int, phase: int) -> None:
    env = sim_env(opcode, phase)
    for i in range(5):
        ctx.set(f"net_opc{i}", env[f"opc{i}"])
    ctx.set("net_ph0", env["ph0"])
    ctx.set("net_ph1", env["ph1"])


def _read_cyclesim(ctx: SimContext) -> dict[str, bool]:
    return {sig: bool(ctx.get(net) & H) for sig, net in CYCLESIM_NET_MAP.items()}


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_lut_eval_matches_row_bools(row, lut_equations: dict[str, str]) -> None:
    lut = _lut_from_eval(row, lut_equations)
    expected = row_bools(row)
    for sig in FSM_OUTPUT_SIGNALS:
        assert lut[sig] == expected[sig], f"{sig} idx5={row.idx5}"


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_merge_matches_ctrl_lookup(row, lut_equations: dict[str, str]) -> None:
    lut = _lut_from_eval(row, lut_equations)
    expected = merge_lut_strobes_from(lut, row.opcode)
    ctx = SimContext()
    ctrl = CtrlLookup()
    ctx.add_block(ctrl)
    ctrl.load_opcode_phase(row.opcode, row.phase)
    _drive_cyclesim(ctx, row.opcode, row.phase)
    ctrl.eval_comb(ctx)
    ctx.comb_fixup()
    got = _read_cyclesim(ctx)
    for sig in MERGE_PIN_SIGNALS:
        assert got[sig] == expected[sig], f"{sig} idx5={row.idx5}"


def merge_lut_strobes_from(lut: dict[str, bool], opcode: int) -> dict[str, bool]:
    from fsm_golden import merge_lut_strobes

    return merge_lut_strobes(lut, opcode)


@pytest.mark.parametrize("opcode", sorted(TFR_OPS), ids=lambda op: f"0x{op:02X}")
def test_tfr_merge_lut_all_low(opcode: int, lut_equations: dict[str, str]) -> None:
    lut = {sig: eval_ctrl_lut_signal(lut_equations, sig, opcode, 0) for sig in FSM_OUTPUT_SIGNALS}
    assert not any(lut.values())
    merged = merged_bools(opcode, 0)
    assert merged["reg_we"] is True
    ctx = SimContext()
    ctrl = CtrlLookup()
    ctx.add_block(ctrl)
    ctrl.load_opcode_phase(opcode, 0)
    _drive_cyclesim(ctx, opcode, 0)
    ctrl.eval_comb(ctx)
    ctx.comb_fixup()
    got = _read_cyclesim(ctx)
    for sig in MERGE_PIN_SIGNALS:
        assert got[sig] == merged[sig], sig


@pytest.mark.parametrize(
    "opcode,phase,flg_z,expect_load",
    [
        (OP_BEQ, 1, True, True),
        (OP_BEQ, 1, False, False),
        (OP_JMP, 0, False, True),
    ],
)
def test_pc_load_macro_end_gating(opcode: int, phase: int, flg_z: bool, expect_load: bool) -> None:
    from fsm_golden import golden_for_opcode_phase

    lut = golden_for_opcode_phase(opcode, phase)
    assert pc_load_at_macro_end(lut, flg_z) == expect_load

    ctx = SimContext()
    branch = BranchAnd()
    ctx.add_block(branch)
    ctx.set("net_macro_end", H)
    ctx.set("net_pc_load_en", H if lut["lut_pc_load"] else L)
    ctx.set("net_pc_load_flg_z", H if lut["lut_pc_flg_z"] else L)
    ctx.set("net_flg_z", H if flg_z else L)
    branch.eval_comb(ctx)
    ctx.comb_fixup()
    got_load = bool(ctx.get("net_pc_load") & H)
    assert got_load == expect_load


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_merged_bools_match_cyclesim_bools(row) -> None:
    from fsm_golden import golden_for_opcode_phase, merge_lut_strobes

    merged = merge_lut_strobes(golden_for_opcode_phase(row.opcode, row.phase), row.opcode)
    ctrl = cyclesim_bools(row.opcode, row.phase)
    for sig in MERGE_PIN_SIGNALS:
        assert merged[sig] == ctrl[sig], f"{sig} idx5={row.idx5}"
