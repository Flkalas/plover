"""idx5 FSM table — M3a-control-store.md (Gi1 v1.0)."""

from __future__ import annotations

import pytest

from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots, lookup_row
from simulators.cyclesim.data.isa import is_reserved_opcode


def test_idx5_slot_count() -> None:
    assert len(active_idx5_slots()) == 22


def test_idx5_unique() -> None:
    slots = [r.idx5 for r in FSM_ROWS]
    assert len(slots) == len(set(slots))


@pytest.mark.parametrize(
    "opcode,phase,expect_idx5",
    [
        (0x01, 0, 4),
        (0x01, 2, 6),
        (0x02, 0, 8),
        (0x06, 0, 24),
        (0x07, 0, 28),
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
    assert r0 and not r0.reg_we
    assert r1 and not r1.reg_we
    assert r2 and r2.y_oe and r2.reg_we and r2.w_sel == 0 and r2.flg_we


def test_cmp_phase_strobes() -> None:
    r0 = lookup_row(0x0D, 0)
    r1 = lookup_row(0x0D, 1)
    r2 = lookup_row(0x0D, 2)
    assert r0 and not r0.reg_we
    assert r1 and not r1.reg_we
    assert r2 and r2.flg_we and not r2.reg_we


def test_call_ret_pc_load() -> None:
    call = lookup_row(0x06, 0)
    ret = lookup_row(0x07, 0)
    assert call and call.pc_load_en and not call.pc_load_flg_z
    assert ret and ret.pc_load_en and not ret.pc_load_flg_z


def test_reserved_opcodes_invalid() -> None:
    for op in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A):
        assert is_reserved_opcode(op)
        assert lookup_row(op, 0) is None
