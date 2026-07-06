"""Tier C CW latch pack parity vs control-word-latch.md bit map."""

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
    CW_HI_BITS,
    CW_LO_BITS,
    merged_for_cw_pack,
    pack_cw_hi,
    pack_cw_lo,
)
from simulators.cyclesim.data.fsm_table import FSM_ROWS
from simulators.cyclesim.data.isa import OP_ADD, OP_BEQ, OP_LDA


def _bit(name: str, merged: dict[str, bool]) -> bool:
    return bool(merged.get(name, False))


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"op{r.opcode:02x}_ph{r.phase}")
def test_active_row_cw_pack_matches_merged(row) -> None:
    merged = merged_for_cw_pack(row.opcode, row.phase, macro_end=False)
    lo = pack_cw_lo(merged)
    hi = pack_cw_hi(merged)
    for i, name in enumerate(CW_LO_BITS):
        assert bool(lo & (1 << i)) == _bit(name, merged), name
    for i, name in enumerate(CW_HI_BITS):
        assert bool(hi & (1 << i)) == _bit(name, merged), name


def test_add_ph0_spot_check() -> None:
    merged = merged_for_cw_pack(OP_ADD, 0)
    # y_oe + bctrl2 in CW_LO (bctrl0..3 fanout; ADD bctrl=1100 -> bctrl2=1)
    assert pack_cw_lo(merged) == (1 << 2) | (1 << 7)
    assert pack_cw_hi(merged) == 0


def test_add_ph2_flg_we() -> None:
    merged = merged_for_cw_pack(OP_ADD, 2)
    assert pack_cw_lo(merged) == (1 << 2) | (1 << 3) | (1 << 7)  # y_oe + flg_we + bctrl2
    assert pack_cw_hi(merged) == 0


def test_lda_ph0_mem_rd() -> None:
    merged = merged_for_cw_pack(OP_LDA, 0)
    assert pack_cw_lo(merged) == 1 << 0  # mem_rd
    assert pack_cw_hi(merged) == 0


def test_beq_macro_end_pc_load_with_flg_z() -> None:
    merged = merged_for_cw_pack(OP_BEQ, 1, macro_end=True, flg_z=True)
    assert pack_cw_lo(merged) == 1 << 4  # pc_load_en
    merged_nz = merged_for_cw_pack(OP_BEQ, 1, macro_end=True, flg_z=False)
    assert pack_cw_lo(merged_nz) == 0
