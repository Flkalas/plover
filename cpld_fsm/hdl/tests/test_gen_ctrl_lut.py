"""Codegen ctrl_lut.inc matches fsm_table.py active rows."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots

HDL = Path(__file__).resolve().parents[1]
REPO = HDL.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(HDL) not in sys.path:
    sys.path.insert(0, str(HDL))

from gen_ctrl_lut import idx5_minterm  # noqa: E402
from sim_fsm_eval import load_ctrl_lut_equations  # noqa: E402

GEN = HDL / "gen_ctrl_lut.py"
LUT = HDL / "ctrl_lut.inc"

BOOL_SIGNALS = (
    "reg_we_lut",
    "mem_rd",
    "mem_wr",
    "y_oe",
    "w_sel0_lut",
    "w_sel1_lut",
    "cin",
    "bctrl0",
    "bctrl2",
    "lgc0",
    "lgc1",
    "lgc2",
    "lgc3",
    "s0",
    "s1",
    "lut_pc_load",
    "lut_pc_flg_z",
    "flg_we",
)


def _row_bools(row) -> dict[str, bool]:
    return {
        "reg_we_lut": row.reg_we,
        "mem_rd": row.mem_rd,
        "mem_wr": row.mem_wr,
        "y_oe": row.y_oe,
        "w_sel0_lut": bool(row.w_sel & 1),
        "w_sel1_lut": bool((row.w_sel >> 1) & 1),
        "cin": bool(row.alu.cin),
        "bctrl0": bool((row.alu.bctrl >> 0) & 1),
        "bctrl2": bool((row.alu.bctrl >> 2) & 1),
        "lgc0": bool((row.alu.lgc >> 0) & 1),
        "lgc1": bool((row.alu.lgc >> 1) & 1),
        "lgc2": bool((row.alu.lgc >> 2) & 1),
        "lgc3": bool((row.alu.lgc >> 3) & 1),
        "s0": bool(row.alu.s0),
        "s1": bool(row.alu.s1),
        "lut_pc_load": row.pc_load_en,
        "lut_pc_flg_z": row.pc_load_flg_z,
        "flg_we": row.flg_we,
    }


def test_active_slot_count() -> None:
    assert len(active_idx5_slots()) == 20


def test_codegen_idempotent() -> None:
    before = LUT.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(GEN)], check=True, cwd=HDL.parents[1])
    after = LUT.read_text(encoding="utf-8")
    assert before == after


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_lut_contains_row(row) -> None:
    text = LUT.read_text(encoding="utf-8")
    equations = load_ctrl_lut_equations(LUT)
    minterm = idx5_minterm(row.idx5)
    flags = _row_bools(row)
    active_any = any(flags.values())
    if active_any:
        assert minterm in text, f"missing minterm for idx5={row.idx5:02d}"
    assert "FIELD idx5" not in text
    assert "idx5 :" not in text
    for sig in BOOL_SIGNALS:
        assert sig in equations, f"missing {sig} equation"
        rhs = equations[sig]
        if flags[sig]:
            assert minterm in rhs, f"{sig} missing minterm for idx5={row.idx5:02d}"
        elif rhs.strip() not in ("0", "'b'0"):
            assert minterm not in rhs, f"{sig} should not include inactive idx5={row.idx5:02d}"
