"""Tests for ustep_ipc_model — research desk model."""

from __future__ import annotations

import pytest

from ustep_ipc_model import (
    MIX_BALANCED,
    evaluate,
    uplift_pct,
)


def test_add_baseline_three_sys_cycles():
    r = evaluate(["ADD"] * 3, ustep=False)
    assert r.sys_cycles == 9
    assert r.ipc == pytest.approx(1 / 3)


def test_add_ustep_one_sys_execute_sync0():
    base = evaluate(["ADD"] * 10, ustep=False)
    u = evaluate(["ADD"] * 10, ustep=True, sync_latency_sys=0)
    assert u.sys_cycles == 10  # 1 SYS per ADD
    assert u.ipc == pytest.approx(1.0)
    assert uplift_pct(base, u) == pytest.approx(200.0)  # 0.67M -> 2.0M


def test_add_ustep_sync1_halves_peak_ipc():
    u = evaluate(["ADD"] * 10, ustep=True, sync_latency_sys=1)
    assert u.sys_cycles == 20  # 1 execute + 1 sync tax
    assert u.ipc == pytest.approx(0.5)


def test_mem_ld_no_uplift_without_sync_tax():
    base = evaluate(["MEM_LD"] * 5, ustep=False)
    u = evaluate(["MEM_LD"] * 5, ustep=True, sync_latency_sys=0)
    assert u.sys_cycles == base.sys_cycles
    assert uplift_pct(base, u) == pytest.approx(0.0)


def test_mem_ld_sync1_is_regression():
    base = evaluate(["MEM_LD"] * 5, ustep=False)
    u = evaluate(["MEM_LD"] * 5, ustep=True, sync_latency_sys=1)
    assert uplift_pct(base, u) < 0


def test_balanced_mix_uplift_positive_sync0():
    base = evaluate(MIX_BALANCED, ustep=False)
    u = evaluate(MIX_BALANCED, ustep=True, sync_latency_sys=0)
    assert uplift_pct(base, u) > 5.0
