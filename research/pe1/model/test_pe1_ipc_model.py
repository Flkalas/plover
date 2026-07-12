"""Tests for PE1 IPC model."""

from __future__ import annotations

import pytest

from pe1_ipc_model import evaluate, pe1_sys


def test_add_cold_two_sys():
    assert pe1_sys("ADD", alu_stream=False) == 2


def test_add_stream_one_sys():
    assert pe1_sys("ADD", alu_stream=True) == 1


def test_alu_stream_ipc_approaches_one():
    r = evaluate(["ADD"] * 50, mode="pe1", alu_stream=True)
    assert r.ipc == pytest.approx(1.0)


def test_lda_includes_mem_stall():
    assert pe1_sys("LDA") == 3  # 1+1+1


def test_taken_beq_costs_more_than_not_taken():
    assert pe1_sys("BEQ", taken=True) > pe1_sys("BEQ", taken=False)


def test_pe1_beats_gi1_on_alu_stream():
    mix = ["ADD"] * 20
    g = evaluate(mix, mode="gi1")
    p = evaluate(mix, mode="pe1", alu_stream=True)
    assert p.macros_per_s > g.macros_per_s
    assert p.ipc > g.ipc
