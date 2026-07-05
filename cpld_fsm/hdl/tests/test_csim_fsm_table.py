"""fsm_table.py golden vs ctrl_lut.inc (CUPL/csim LUT) and cyclesim CtrlLookup."""

from __future__ import annotations

import subprocess
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
    row_bools,
    sim_env,
)
from sim_fsm_eval import eval_ctrl_lut_signal, load_ctrl_lut_equations
from simulators.cyclesim.blocks.fsm import CtrlLookup
from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H

GEN_SI = HDL / "gen_csim_si.py"
SI = HDL / "system_ctrl_gen.si"
LUT = HDL / "ctrl_lut.inc"


def _drive_cyclesim_inputs(ctx: SimContext, opcode: int, phase: int) -> None:
    env = sim_env(opcode, phase)
    for i in range(5):
        ctx.set(f"net_opc{i}", env[f"opc{i}"])
    ctx.set("net_ph0", env["ph0"])
    ctx.set("net_ph1", env["ph1"])


def _read_cyclesim_outputs(ctx: SimContext) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for sig, net in CYCLESIM_NET_MAP.items():
        out[sig] = bool(ctx.get(net) & H)
    return out


@pytest.fixture(scope="module")
def lut_equations() -> dict[str, str]:
    if not LUT.is_file():
        pytest.skip(f"missing {LUT.name} — run gen_ctrl_lut.py first")
    return load_ctrl_lut_equations(LUT)


def test_gen_csim_si_idempotent() -> None:
    before = SI.read_text(encoding="utf-8") if SI.is_file() else ""
    subprocess.run([sys.executable, str(GEN_SI)], check=True, cwd=REPO)
    after = SI.read_text(encoding="utf-8")
    if before:
        assert before == after


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_ctrl_lut_eval_matches_fsm_table(row, lut_equations: dict[str, str]) -> None:
    expected = row_bools(row)
    for sig in FSM_OUTPUT_SIGNALS:
        got = eval_ctrl_lut_signal(lut_equations, sig, row.opcode, row.phase)
        assert got == expected[sig], f"{sig} idx5={row.idx5}"


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_cyclesim_ctrl_lookup_matches_fsm_table(row) -> None:
    ctx = SimContext()
    ctrl = CtrlLookup()
    ctx.add_block(ctrl)
    ctrl.load_opcode_phase(row.opcode, row.phase)
    _drive_cyclesim_inputs(ctx, row.opcode, row.phase)
    ctrl.eval_comb(ctx)
    ctx.comb_fixup()
    got = _read_cyclesim_outputs(ctx)
    expected = cyclesim_bools(row.opcode, row.phase)
    for sig in CYCLESIM_NET_MAP:
        assert got[sig] == expected[sig], f"{sig} idx5={row.idx5}"


@pytest.mark.parametrize("idx5", [slot for slot in range(128) if slot not in set(active_idx5_slots())][:3])
def test_cyclesim_inactive_idx5(idx5: int) -> None:
    opcode = (idx5 >> 2) & 0x1F
    phase = idx5 & 3
    ctx = SimContext()
    ctrl = CtrlLookup()
    ctx.add_block(ctrl)
    assert ctrl.load_opcode_phase(opcode, phase) is None
    _drive_cyclesim_inputs(ctx, opcode, phase)
    ctrl.eval_comb(ctx)
    ctx.comb_fixup()
    for sig, net in CYCLESIM_NET_MAP.items():
        if sig in ("lut_pc_load", "lut_pc_flg_z"):
            continue
        assert not (ctx.get(net) & H), f"{sig} idx5={idx5} inactive"

