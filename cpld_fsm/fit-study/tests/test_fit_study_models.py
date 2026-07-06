"""Research-only tests — v1.0 cpld_fsm/hdl/tests unchanged."""

from __future__ import annotations

import sys
from pathlib import Path

FIT_STUDY = Path(__file__).resolve().parents[1]
ROOT = FIT_STUDY.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FIT_STUDY))

from sim.eeprom_cw import EepromCtrlStore  # noqa: E402
from sim.external_gpr import ExternalGpr574  # noqa: E402

from cpld_fsm.hdl.fsm_golden import (  # noqa: E402
    merged_for_cw_pack,
    pack_cw_hi,
    pack_cw_lo,
)
from simulators.cyclesim.data.fsm_table import FSM_ROWS  # noqa: E402


def test_eeprom_cw_matches_fsm_golden():
    store = EepromCtrlStore()
    for row in FSM_ROWS:
        merged = merged_for_cw_pack(row.opcode, row.phase, macro_end=True, flg_z=True)
        lo, hi = store.lookup(row.opcode, row.phase)
        assert lo == pack_cw_lo(merged), f"CW_LO opcode={row.opcode:#x} ph={row.phase}"
        assert hi == pack_cw_hi(merged), f"CW_HI opcode={row.opcode:#x} ph={row.phase}"


def test_external_gpr_fixed_read():
    gpr = ExternalGpr574()
    gpr.write(0, 0x12, True)
    gpr.write(1, 0x34, True)
    assert gpr.q_a == 0x12
    assert gpr.q_b == 0x34
    gpr.write(2, 0xAB, True)
    assert gpr.read_reg(2) == 0xAB
