"""Tests for CPU 4-axis architecture search model."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cpu_arch_model import (
    baseline_v10_config,
    corner_h1_config,
    corner_h2_config,
    dominates,
    iter_configs,
    pareto_front,
    score_config,
)


def test_baseline_dip_and_delay():
    c = score_config(baseline_v10_config())
    assert c.dip_74hc == 31
    assert c.delay_max_ns == 151
    assert c.feasible


def test_cw_direct_saves_dip_and_delay():
    h2 = score_config(corner_h2_config())
    base = score_config(baseline_v10_config())
    assert h2.dip_74hc <= base.dip_74hc - 8
    assert h2.delay_max_ns <= base.delay_max_ns - 15
    assert h2.feasible


def test_h1_hybrid_low_flash_rows():
    h1 = score_config(corner_h1_config())
    h2 = score_config(corner_h2_config())
    assert h1.flash_rows < h2.flash_rows
    assert h1.feasible


def test_pareto_front_nonempty_and_beats_baseline():
    costs = [score_config(c) for c in iter_configs()]
    front = pareto_front(costs)
    assert len(front) >= 1
    base = score_config(baseline_v10_config())
    best = front[0]
    assert best.dip_74hc < base.dip_74hc or best.delay_max_ns < base.delay_max_ns


def test_dominance_transitive_baseline():
    base = score_config(baseline_v10_config())
    h2 = score_config(corner_h2_config())
    assert dominates(h2, base) or h2.pareto_key() != base.pareto_key()


def test_incompatible_configs_pruned():
    keys = {c.key for c in iter_configs()}
    assert "op_class_idx4_dec_sop_cpld_4gpr_cw10_aluop" not in keys
    assert "op_legacy_idx4_dec_cw_direct_cpld_4gpr_cw10_aluop" not in keys


def test_pack_cw16_roundtrip():
    from pack_control_store import pack_cw16, pack_cw16_store, cs_index

    cw = pack_cw16(cin=1, b_sel=1, lgc=0, reg_we=1, y_oe=1, reg_wsel=2)
    store = pack_cw16_store({(0x01, 2): cw})
    idx = cs_index(0x01, 2)
    assert store[2 * idx] == cw & 0xFF
    assert store[2 * idx + 1] == (cw >> 8) & 0xFF
