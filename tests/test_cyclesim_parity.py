"""cyclesim datapath vs plover_vm micro — hwsim/cyclesim normative GPR semantics."""

from __future__ import annotations

from pathlib import Path

from cyclesim.engine import build_context
from cyclesim.micro_driver import apply_micro_phase
from cyclesim.runner import _drive_operand_b
from plover_vm.alu import alu8
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.nor import CW_FLASH_BASE
from plover_vm.micro.engine import MicroEngine
from tools.pack_control_store import build_all

ROOT = Path(__file__).resolve().parents[1]
DATAPATH = ROOT / "hw/netlist/blocks/datapath_p1.yaml"


def _load_control_store(bus: MemoryBus) -> None:
    for idx, cw in enumerate(build_all()):
        bus.nor._mem[CW_FLASH_BASE + idx] = cw & 0xFF


def _run_cyclesim_add_imm() -> list[int]:
    ctx = build_context(DATAPATH, ROOT)
    ctx.regfile.set_gpr(0, 0x12)
    ctx.regfile.set_gpr(1, 0x34)
    for ph in range(3):
        ctx._stuck_nets.clear()
        ctx.reset_float_nets()
        apply_micro_phase(ctx, 0x01, ph, 0x34)
        _drive_operand_b(ctx, 0x01, ph, 0x34)
        ctx.comb_fixup()
        if ph == 2:
            ctx.pulse_clock()
    return [ctx.regfile.get_gpr(i) for i in range(4)]


def _run_micro_add_imm() -> tuple[list[int], int]:
    bus = MemoryBus()
    _load_control_store(bus)
    micro = MicroEngine(bus)
    micro.reset_micro(0x01, 0x34)
    micro.state.regs[0] = 0x12
    micro.state.regs[1] = 0x34
    for _ in range(3):
        micro.step()
    return list(micro.state.regs), micro.state.alu_y


def test_add_imm_datapath_matches_alu8():
    assert alu8(0x12, 0x34, 1).y == 0x46
    gpr = _run_cyclesim_add_imm()
    assert gpr[2] == 0x46


def test_add_imm_vm_matches_cyclesim_and_alu8():
    gpr_cs = _run_cyclesim_add_imm()
    gpr_vm, alu_y = _run_micro_add_imm()
    assert alu_y == 0x46
    assert gpr_vm == gpr_cs
    assert gpr_vm[2] == 0x46
