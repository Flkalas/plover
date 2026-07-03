"""idx5 FSM table — M3a-control-store.md."""

from __future__ import annotations

import pytest

from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots, lookup_row


def test_idx5_slot_count() -> None:
    assert len(active_idx5_slots()) == 26


def test_idx5_unique() -> None:
    slots = [r.idx5 for r in FSM_ROWS]
    assert len(slots) == len(set(slots))


@pytest.mark.parametrize(
    "opcode,phase,expect_idx5",
    [
        (0x01, 0, 4),
        (0x01, 2, 6),
        (0x02, 0, 8),
        (0x14, 0, 80),
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
    assert r1 and r1.y_oe and r1.reg_we_r1
    assert r2 and r2.reg_we and r2.w_sel == 2 and r2.flg_we


def test_tfr20_row() -> None:
    row = lookup_row(0x14, 0)
    assert row is not None
    assert row.template.value == "XFER"
    assert row.reg_we and row.w_sel == 2
