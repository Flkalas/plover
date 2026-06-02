"""Drive nets from opcode × phase control word (v0.1 pack_control_store)."""

from __future__ import annotations

import sys
from pathlib import Path

from cyclesim.engine import CycleContext
from plover_vm.micro.cw import ControlWord
from plover_vm.micro.reg_sel import reg_sel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.pack_control_store import build_all, cs_index  # noqa: E402

_CW_STORE: list[int] | None = None


def _cw_store() -> list[int]:
    global _CW_STORE
    if _CW_STORE is None:
        _CW_STORE = build_all()
    return _CW_STORE


def lookup_cw(opcode: int, phase: int) -> ControlWord:
    idx = cs_index(opcode & 0xF, phase & 3)
    return ControlWord(_cw_store()[idx])


def apply_micro_phase(
    ctx: CycleContext,
    opcode: int,
    phase: int,
    operand: int = 0,
) -> None:
    """Apply CW + Reg_Sel read ports + optional ADD operand→R1 (VM ph0 rule)."""
    cw = lookup_cw(opcode, phase)
    sel = reg_sel(opcode, phase)

    for i in range(4):
        ctx.set_net(f"net_alu_op{i}", (cw.alu_op >> i) & 1, stuck=True)

    ctx.set_net("net_reg_we", 1 if cw.reg_we else 0, stuck=True)
    ctx.set_net("net_y_oe", 1 if cw.y_oe else 0, stuck=True)
    ctx.set_net("net_mem_rd", 1 if cw.mem_rd else 0, stuck=True)
    ctx.set_net("net_mem_wr", 1 if cw.mem_wr else 0, stuck=True)

    for r in range(4):
        ctx.set_net(f"net_load_r{r}", 0, stuck=True)
    if cw.reg_we:
        ctx.set_net(f"net_load_r{sel}", 1, stuck=True)

    ra, rb = _read_ports(opcode, phase, operand)
    ctx.set_net("net_ra0", ra & 1, stuck=True)
    ctx.set_net("net_ra1", (ra >> 1) & 1, stuck=True)
    ctx.set_net("net_rb0", rb & 1, stuck=True)
    ctx.set_net("net_rb1", (rb >> 1) & 1, stuck=True)

    if opcode == 0x01 and phase == 0 and operand:
        if ctx.regfile is not None:
            ctx.regfile.set_gpr(1, operand & 0xFF)


def _read_ports(opcode: int, phase: int, operand: int) -> tuple[int, int]:
    op = opcode & 0xFF
    if op == 0x01:
        return 0, 1
    if op == 0x0D:
        if phase == 0:
            return 0, 0
        if phase == 1:
            return 0, 0
    if op == 0x04:
        return 0, 0
    if op in (0x02, 0x03, 0x08, 0x09):
        return 0, 0
    return reg_sel(op, phase), 0


def should_pulse_clock(ctx: CycleContext, opcode: int, phase: int) -> bool:
    cw = lookup_cw(opcode, phase)
    return bool(cw.reg_we and reg_sel(opcode, phase) < 4)
