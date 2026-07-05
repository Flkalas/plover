"""Codegen ctrl_lut.vhd matches fsm_table.py active rows."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots

HDL = Path(__file__).resolve().parents[1]
GEN = HDL / "gen_ctrl_lut.py"
LUT = HDL / "ctrl_lut.vhd"


def test_active_slot_count() -> None:
    assert len(active_idx5_slots()) == 26


def test_codegen_idempotent() -> None:
  before = LUT.read_text(encoding="utf-8")
  subprocess.run([sys.executable, str(GEN)], check=True, cwd=HDL.parents[1])
  after = LUT.read_text(encoding="utf-8")
  assert before == after


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_lut_contains_row(row) -> None:
    text = LUT.read_text(encoding="utf-8")
    block = re.search(rf"^\s*{row.idx5}\s*=>\s*\(", text, re.MULTILINE)
    assert block, f"missing LUT slot {row.idx5}"
    start = block.start()
    snippet = text[start : start + 400]
    if row.reg_we:
        assert "reg_we => '1'" in snippet
    if row.mem_rd:
        assert "mem_rd => '1'" in snippet
    if row.alu.cin:
        assert "cin => '1'" in snippet
    assert f'bctrl => "{row.alu.bctrl:04b}"' in snippet
