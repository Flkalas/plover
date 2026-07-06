"""CUPL .sim %EQUATION outputs vs fsm_table golden (post build-wincupl.ps1)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HDL = Path(__file__).resolve().parents[1]
REPO = HDL.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(HDL) not in sys.path:
    sys.path.insert(0, str(HDL))

from fsm_golden import FSM_OUTPUT_SIGNALS, golden_for_opcode_phase
from sim_fsm_eval import eval_signal, load_sim_equations
from simulators.cyclesim.data.fsm_table import FSM_ROWS

SIM = HDL / "system_ctrl_cu_gen.sim"


def _sim_env(opcode: int, phase: int) -> dict[str, int]:
    op = opcode & 0x1F
    ph = phase & 3
    env: dict[str, int] = {f"opc{i}": (op >> i) & 1 for i in range(5)}
    env["ph0"] = ph & 1
    env["ph1"] = (ph >> 1) & 1
    env["flg_z"] = 0
    env["flg_c"] = 0
    env["macro_end"] = 0
    return env


@pytest.fixture(scope="module")
def sim_equations() -> dict[str, str]:
    if not SIM.is_file() or SIM.stat().st_size == 0:
        pytest.skip(f"missing {SIM.name} — run build-wincupl.ps1 first")
    return load_sim_equations(SIM)


@pytest.mark.parametrize("row", FSM_ROWS, ids=lambda r: f"idx5={r.idx5}")
def test_sim_lut_matches_golden(row, sim_equations: dict[str, str]) -> None:
    env = _sim_env(row.opcode, row.phase)
    expected = golden_for_opcode_phase(row.opcode, row.phase)
    for sig in FSM_OUTPUT_SIGNALS:
        if sig not in sim_equations:
            pytest.fail(f"{sig} missing from .sim")
        got = eval_signal(sim_equations, sig, env)
        assert got == expected[sig], f"{sig} idx5={row.idx5:02d} sim={got} golden={expected[sig]}"
