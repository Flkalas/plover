"""TFR ISA variant tests — fit-study."""

from __future__ import annotations

import sys
from pathlib import Path

FIT_STUDY = Path(__file__).resolve().parents[1]
ROOT = FIT_STUDY.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FIT_STUDY))

from sim.tfr_isa_models import (  # noqa: E402
    ALL_TFR_PAIRS,
    TMP,
    decode_tfr_3bit,
    decode_tfr_ring_2bit,
    decode_tfr_ring_macro,
    decode_tfr_tmp_2op,
    decode_tfr_v10,
    encode_tfr_3bit,
    pairs_reachable_ring_2bit,
    pairs_reachable_tmp_2op,
    ring_2bit_cold_expand,
    tfr_tmp_2op_micro_ops,
    v10_opcode_for_pair,
)
from simulators.cyclesim.data.isa import decode_tfr  # noqa: E402


def test_v10_all_pairs():
    for src, dst in ALL_TFR_PAIRS:
        op = v10_opcode_for_pair(src, dst)
        assert decode_tfr_v10(op) == (src, dst)
        assert decode_tfr(op) == (src, dst)


def test_3bit_roundtrip_all_pairs():
    for src, dst in ALL_TFR_PAIRS:
        op = encode_tfr_3bit(src, dst)
        assert decode_tfr_3bit(op) == (src, dst)


def test_ring_2bit_hot_three():
    reachable = pairs_reachable_ring_2bit()
    assert len(reachable) == 3
    assert (1, 0) in reachable
    assert (2, 1) in reachable
    assert (0, 2) in reachable


def test_ring_2bit_cold_needs_two_insn():
    seq = ring_2bit_cold_expand(2, 0)
    assert len(seq) == 2
    assert seq[0] == (2, 1)
    assert seq[1] == (1, 0)


def test_ring_macro_cold_two_hops():
    op = 0x13  # cold sub=00 -> R0<-R2, 2 ring hops (clobber)
    r = decode_tfr_ring_macro(op)
    assert r is not None
    src, dst, hops = r
    assert hops == 2
    assert (src, dst) == (2, 0)


def test_tmp_2op_all_six_pairs():
    assert pairs_reachable_tmp_2op() == set(ALL_TFR_PAIRS)


def test_tmp_2op_micro_no_gpr_clobber():
    ops = tfr_tmp_2op_micro_ops(2, 0)
    assert len(ops) == 2
    assert ops[0][0] == TMP
    assert ops[1][0] == 0  # write R0
    assert ops[0][1] == 2  # read R2


def test_tmp_2op_decode_cold():
    op = 0x13  # 10011: low=11, sub=00 -> R0<-R2
    assert decode_tfr_tmp_2op(op) == (2, 0)
