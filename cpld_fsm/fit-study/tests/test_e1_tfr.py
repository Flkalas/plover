"""E1 TFR + EEPROM integration tests (fit-study)."""

from __future__ import annotations

import sys
from pathlib import Path

FIT_STUDY = Path(__file__).resolve().parents[1]
ROOT = FIT_STUDY.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FIT_STUDY))

from sim.eeprom_cw import EepromCtrlStore  # noqa: E402
from sim.gpr_flash_fsm import E1GprEepromModel, tfr_strobes, tfr_xfer_data  # noqa: E402

from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr  # noqa: E402
from simulators.cyclesim.data.fsm_table import FSM_ROWS  # noqa: E402


def test_eeprom_cw_all_fsm_rows():
    store = EepromCtrlStore()
    model = E1GprEepromModel()
    for row in FSM_ROWS:
        assert model.parity_fsm_row(row.opcode, row.phase)


def test_tfr_six_opcodes_data_path():
    model = E1GprEepromModel()
    model.gpr.regs = [0x10, 0x20, 0x30]
    cases = {
        0x11: (0x20, 0x10),  # R0<-R1
        0x12: (0x30, 0x10),  # R0<-R2
        0x14: (0x10, 0x20),  # R1<-R0
        0x16: (0x30, 0x20),  # R1<-R2
        0x18: (0x10, 0x30),  # R2<-R0
        0x19: (0x20, 0x30),  # R2<-R1
    }
    for op, (exp_src_val, exp_dst_val) in cases.items():
        model.gpr.regs = [0x10, 0x20, 0x30]
        src, dst = decode_tfr(op)
        assert tfr_xfer_data(model.gpr, op) == exp_src_val
        we, w_dst = tfr_strobes(op)
        assert we and w_dst == dst
        model.execute_tfr(op)
        assert model.gpr.read(dst) == exp_src_val
        assert model.gpr.q_a == model.gpr.read(0)
        assert model.gpr.q_b == model.gpr.read(1)


def test_tfr_invalid_opcode_no_write():
    model = E1GprEepromModel()
    model.gpr.regs = [1, 2, 3]
    we, _ = tfr_strobes(0x10)
    assert not we
    model.execute_tfr(0x10)
    assert model.gpr.regs == [1, 2, 3]


def test_tfr_ops_set_matches_v10():
    assert TFR_OPS == frozenset({0x11, 0x12, 0x14, 0x16, 0x18, 0x19})
