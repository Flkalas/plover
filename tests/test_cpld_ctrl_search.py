"""Tests for CPLD control extraction search."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cpld_ctrl_arch import (  # noqa: E402
    ARCH_BASELINE_FSM,
    ARCH_FLASH_CW10,
    ARCH_FLASH_CW16,
    ARCH_SOP_IDX5,
    BASELINE_MC,
    GPR_ONLY_MC,
    IndexWidth,
    pareto_front,
    score_all_configs,
    score_control_arch,
)
from cpld_ctrl_model import active_idx5_slots, build_v10_ctrl_table  # noqa: E402
from pack_control_store import ALU_SUB, OP_ADD, OP_BEQ, OP_LDA  # noqa: E402


def _row(op: int, ph: int):
    for r in build_v10_ctrl_table():
        if r.opcode == op and r.phase == ph:
            return r
    raise KeyError((op, ph))


def test_ctrl_table_row_count_and_idx5_unique():
    rows = build_v10_ctrl_table()
    assert len(rows) == 26
    slots = active_idx5_slots(rows)
    assert len(slots) == 26
    assert len(slots) == len(set(slots))


def test_lda_ph0_mem_rd():
    r = _row(OP_LDA, 0)
    assert r.mem_rd == 1
    assert r.reg_we == 0
    assert r.y_oe == 0


def test_add_ph2_reg_we_wsel():
    r = _row(OP_ADD, 2)
    assert r.reg_we == 1
    assert r.w_sel == 2
    assert r.y_oe == 1


def test_beq_ph0_sub():
    r = _row(OP_BEQ, 0)
    assert r.alu_op == ALU_SUB
    assert r.y_oe == 0
    assert r.cin == 1 and r.b_sel == 1


def test_baseline_fsm():
    c = score_control_arch(ARCH_BASELINE_FSM, IndexWidth.IDX5)
    assert c.feasible
    assert c.cpld_mc == BASELINE_MC
    assert c.dip_74hc == 0
    assert c.flash_rows == 0


def test_gpr_only_archs_mc():
    for idx in IndexWidth:
        assert score_control_arch(ARCH_FLASH_CW10, idx).cpld_mc == GPR_ONLY_MC
        assert score_control_arch(ARCH_FLASH_CW16, idx).cpld_mc == GPR_ONLY_MC
    assert score_control_arch(ARCH_SOP_IDX5, IndexWidth.IDX4).cpld_mc == GPR_ONLY_MC


def test_flash_cw16_fewer_dip_than_cw10():
    c10 = score_control_arch(ARCH_FLASH_CW10, IndexWidth.IDX4)
    c16 = score_control_arch(ARCH_FLASH_CW16, IndexWidth.IDX4)
    assert c16.dip_74hc < c10.dip_74hc


def test_flash_cw16_e2e_timing_fields():
    c = score_control_arch(ARCH_FLASH_CW16, IndexWidth.IDX4)
    assert c.delay_alu_ns == 136
    assert c.delay_fetch_ns == 96
    assert c.delay_execute_ns == 159
    assert c.delay_max_ns == c.delay_execute_ns
    assert c.timing_feasible
    assert c.feasible
    assert any("pipelined" in n.lower() or "serial" in n.lower() for n in c.notes)


def test_sop_idx5_positive_dip():
    c = score_control_arch(ARCH_SOP_IDX5, IndexWidth.IDX4)
    assert c.dip_74hc > 0
    assert c.gates > 0


def test_pareto_front_nonempty():
    costs = score_all_configs()
    front = pareto_front(costs)
    assert front
    assert any(c.arch == ARCH_BASELINE_FSM for c in front)
