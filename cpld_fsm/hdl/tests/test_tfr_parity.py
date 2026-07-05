"""TFR comb parity: isa.TFR_OPS ↔ PLD tfr_valid ↔ cyclesim CtrlLookup."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

HDL = Path(__file__).resolve().parents[1]
REPO = HDL.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(HDL) not in sys.path:
    sys.path.insert(0, str(HDL))

from fsm_golden import CYCLESIM_NET_MAP, cyclesim_bools, sim_env
from simulators.cyclesim.blocks.fsm import CtrlLookup
from simulators.cyclesim.data.fsm_table import FSM_ROWS, active_idx5_slots
from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr
from simulators.cyclesim.engine import SimContext
from simulators.cyclesim.values import H

PLD = HDL / "system_ctrl.pld"
TFR_LITERAL_RE = re.compile(r"'b'([01]{5})")


def _parse_pld_tfr_opcodes() -> set[int]:
    text = PLD.read_text(encoding="utf-8")
    start = text.index("tfr_valid")
    end = text.index("\n\n", start)
    block = text[start:end]
    return {int(m.group(1), 2) for m in TFR_LITERAL_RE.finditer(block)}


def _drive_cyclesim_inputs(ctx: SimContext, opcode: int, phase: int) -> None:
    env = sim_env(opcode, phase)
    for i in range(5):
        ctx.set(f"net_opc{i}", env[f"opc{i}"])
    ctx.set("net_ph0", env["ph0"])
    ctx.set("net_ph1", env["ph1"])


def _read_cyclesim_outputs(ctx: SimContext) -> dict[str, bool]:
    return {sig: bool(ctx.get(net) & H) for sig, net in CYCLESIM_NET_MAP.items()}


def test_tfr_ops_match_pld() -> None:
    assert _parse_pld_tfr_opcodes() == set(TFR_OPS)


def test_active_row_count() -> None:
    assert len(FSM_ROWS) == 20
    assert len(active_idx5_slots()) == 20


@pytest.mark.parametrize(
    "opcode",
    sorted(TFR_OPS),
    ids=lambda op: f"0x{op:02X}",
)
def test_cyclesim_tfr_all_pairs(opcode: int) -> None:
    src, dst = decode_tfr(opcode)
    ctx = SimContext()
    ctrl = CtrlLookup()
    ctx.add_block(ctrl)
    assert ctrl.load_opcode_phase(opcode, 0) is None
    _drive_cyclesim_inputs(ctx, opcode, 0)
    ctrl.eval_comb(ctx)
    ctx.comb_fixup()
    got = _read_cyclesim_outputs(ctx)
    expected = cyclesim_bools(opcode, 0)
    for sig in CYCLESIM_NET_MAP:
        assert got[sig] == expected[sig], f"{sig} TFR{src}{dst} 0x{opcode:02X}"
    assert got["reg_we"] is True
    assert got["w_sel0"] == bool(dst & 1)
    assert got["w_sel1"] == bool((dst >> 1) & 1)
