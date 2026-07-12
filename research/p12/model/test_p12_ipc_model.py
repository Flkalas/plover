"""Tests for P12 IPC model."""

from __future__ import annotations

import pytest

from p12_ipc_model import evaluate, p12_sys, pe1_sys


def test_p12_matches_pe1_optimistic():
    for name in ("ADD", "LDA", "BEQ", "CALL", "RET"):
        assert p12_sys(name, taken=True) == pe1_sys(name, taken=True)
        assert p12_sys(name, taken=False) == pe1_sys(name, taken=False)


def test_alu_stream_ipc_one():
    r = evaluate(["ADD"] * 50, mode="p12", alu_stream=True)
    assert r.ipc == pytest.approx(1.0)


def test_stretch_adds_on_lda():
    assert p12_sys("LDA", stretch=True) == p12_sys("LDA", stretch=False) + 1


def test_stretch_beq_only_when_taken():
    assert p12_sys("BEQ", taken=True, stretch=True) == p12_sys("BEQ", taken=True) + 1
    assert p12_sys("BEQ", taken=False, stretch=True) == p12_sys("BEQ", taken=False)


def test_fallback_equals_fe2():
    mix = ["ADD"] * 10
    assert evaluate(mix, mode="fallback_fe2").sys_cycles == evaluate(
        mix, mode="fe2"
    ).sys_cycles


def test_p12_beats_fallback_on_alu_stream():
    mix = ["ADD"] * 20
    p = evaluate(mix, mode="p12", alu_stream=True)
    fb = evaluate(mix, mode="fallback_fe2")
    assert p.macros_per_s > fb.macros_per_s
