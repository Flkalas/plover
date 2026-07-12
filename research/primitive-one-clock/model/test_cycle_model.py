"""Tests for primitive one-clock cycle model."""

from __future__ import annotations

import pytest

from cycle_model import OPS, evaluate, total_sys, uplift_pct


def test_add_gi1_includes_idle_and_fetch():
    # 2 fetch + 3 exec
    n, c = total_sys(["ADD"], "gi1")
    assert n == 1 and c == 5


def test_add_fe2_drops_idle():
    # 2 fetch + 1 exec
    n, c = total_sys(["ADD"], "fe2")
    assert n == 1 and c == 3


def test_add_fe1_wishful_one():
    n, c = total_sys(["ADD"], "fe1")
    assert c == 1
    assert OPS["ADD"].fe1_possible is False


def test_no_op_claims_fe1_possible():
    assert all(not op.fe1_possible for op in OPS.values())


def test_fe2_beats_gi1_on_alu_stream():
    mix = ["ADD"] * 10
    g = evaluate(mix, "gi1")
    f2 = evaluate(mix, "fe2")
    assert f2.macros_per_s > g.macros_per_s
    assert uplift_pct(g, f2) == pytest.approx(66.666, rel=1e-3)


def test_balanced_fe2_uplift_positive():
    mix = ["ADD", "LDA", "ADD", "CMP", "STA", "BEQ", "ADD", "JMP"]
    g = evaluate(mix, "gi1")
    f2 = evaluate(mix, "fe2")
    assert f2.sys_cycles < g.sys_cycles
    assert f2.macros_per_s > g.macros_per_s
