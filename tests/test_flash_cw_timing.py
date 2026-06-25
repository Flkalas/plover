"""Flash CW end-to-end timing budget tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from flash_cw_timing import (  # noqa: E402
    ARCH_BASELINE_FSM,
    ARCH_FLASH_CW10,
    ARCH_FLASH_CW16,
    EXEC_HALF_NS,
    budget_for_arch,
)


def test_baseline_fsm_pipelined_ok():
    b = budget_for_arch(ARCH_BASELINE_FSM)
    assert b.pipelined_ok
    assert b.delay_execute_ns <= EXEC_HALF_NS


def test_flash_cw16_pipelined_ok_serial_fails():
    b = budget_for_arch(ARCH_FLASH_CW16)
    assert b.pipelined_ok
    assert not b.serial_ok
    assert b.delay_fetch_ns <= EXEC_HALF_NS
    assert b.delay_execute_ns <= EXEC_HALF_NS
    assert b.serial_total_ns > EXEC_HALF_NS


def test_flash_cw10_pipelined_ok():
    b = budget_for_arch(ARCH_FLASH_CW10)
    assert b.pipelined_ok
    assert b.delay_execute_ns <= EXEC_HALF_NS


@pytest.mark.parametrize(
    "arch",
    [ARCH_FLASH_CW16, ARCH_FLASH_CW10],
)
def test_flash_arch_execute_slack_positive(arch: str):
    b = budget_for_arch(arch)
    assert b.pipelined_execute_slack_ns > 0
