"""idx5 FSM table — M3a-control-store.md."""

from __future__ import annotations

import pytest

from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots, lookup_row
from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr, encode_tfr, is_tfr_valid


def test_idx5_slot_count() -> None:
    assert len(active_idx5_slots()) == 20


def test_idx5_unique() -> None:
    slots = [r.idx5 for r in FSM_ROWS]
    assert len(slots) == len(set(slots))


@pytest.mark.parametrize(
    "opcode,phase,expect_idx5",
    [
        (0x01, 0, 4),
        (0x01, 2, 6),
        (0x02, 0, 8),
    ],
)
def test_frozen_idx5(opcode: int, phase: int, expect_idx5: int) -> None:
    row = lookup_row(opcode, phase)
    assert row is not None
    assert row.idx5 == expect_idx5


def test_add_phase_strobes() -> None:
    r0 = lookup_row(0x01, 0)
    r1 = lookup_row(0x01, 1)
    r2 = lookup_row(0x01, 2)
    assert r0 and r0.y_oe and not r0.reg_we
    assert r1 and r1.y_oe and r1.reg_we and r1.w_sel == 1
    assert r2 and r2.reg_we and r2.w_sel == 2 and r2.flg_we


@pytest.mark.parametrize(
    "opcode,src,dst",
    [
        (0x11, 1, 0),
        (0x12, 2, 0),
        (0x14, 0, 1),
        (0x16, 2, 1),
        (0x18, 0, 2),
        (0x19, 1, 2),
    ],
)
def test_tfr_bit_field(opcode: int, src: int, dst: int) -> None:
    assert opcode in TFR_OPS
    assert is_tfr_valid(opcode)
    assert decode_tfr(opcode) == (src, dst)
    assert encode_tfr(src, dst) == opcode
    assert lookup_row(opcode, 0) is None


def test_tfr_invalid_reserved() -> None:
    for op in (0x10, 0x13, 0x15, 0x17, 0x1A):
        assert not is_tfr_valid(op)
