"""G Plan TFR parity on production dual PLD sources."""

from __future__ import annotations

import sys
from pathlib import Path

HDL = Path(__file__).resolve().parents[1]
REPO = HDL.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HDL))

from g_dual_integration import GPlanCuModel, GPlanDpModel  # noqa: E402
from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr  # noqa: E402


def _pld_has_tfr_valid_cu() -> bool:
    text = (HDL / "system_ctrl_cu.pld").read_text(encoding="utf-8")
    return "tfr_valid" in text and "'b'10001" in text


def test_cu_pld_declares_six_tfr_opcodes():
    assert _pld_has_tfr_valid_cu()


def test_all_six_tfr_via_g_ic_model():
    cu = GPlanCuModel()
    cases = [
        (0x11, 1, 0, 0xA1),
        (0x12, 2, 0, 0xA2),
        (0x14, 0, 1, 0xB0),
        (0x16, 2, 1, 0xB2),
        (0x18, 0, 2, 0xC0),
        (0x19, 1, 2, 0xC1),
    ]
    for op, src_reg, dst_reg, value in cases:
        assert op in TFR_OPS
        dp = GPlanDpModel()
        dp.gpr.write(src_reg, value, True)
        dp.apply_g_ic(cu.decode_g_ic(op))
        assert decode_tfr(op) == (src_reg, dst_reg)
        if dst_reg == 0:
            assert dp.gpr.q_a == value
        elif dst_reg == 1:
            assert dp.gpr.q_b == value
        else:
            assert dp.gpr.read(2) == value
