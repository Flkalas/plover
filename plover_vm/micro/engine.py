"""One micro-phase execution step."""

from __future__ import annotations

from dataclasses import dataclass, field

from plover_vm.alu import alu8
from plover_vm.memory.bus import MemoryBus
from plover_vm.micro.cw import lookup_cw
from plover_vm.micro.reg_sel import reg_sel


@dataclass
class MicroState:
    opcode: int = 0
    operand: int = 0
    phase: int = 0
    regs: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    alu_a: int = 0
    alu_b: int = 0
    alu_y: int = 0
    bus_data: int = 0
    eff_addr: int = 0
    flag_z: bool = False
    flag_c: bool = False


class MicroEngine:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus
        self.state = MicroState()

    def reset_micro(self, opcode: int, operand: int) -> None:
        self.state.opcode = opcode & 0xFF
        self.state.operand = operand & 0xFF
        self.state.phase = 0
        self.state.alu_a = 0
        self.state.alu_b = 0

    def step(self) -> None:
        st = self.state
        op, ph = st.opcode, st.phase
        cw = lookup_cw(self.bus.nor.read_cw, op, ph)
        sel = reg_sel(op, ph)

        if cw.mem_rd:
            st.eff_addr = st.operand & 0xFFFF
            st.bus_data = self.bus.read_cpu(st.eff_addr)

        if op == 0x01 and cw.alu_op:
            if ph == 0 and st.operand:
                st.regs[1] = st.operand & 0xFF
            res = alu8(st.regs[0], st.regs[1], cw.alu_op)
            st.alu_y = res.y
            st.flag_z = res.zero
            st.flag_c = res.cout
        elif cw.y_oe or cw.alu_op:
            ra = st.regs[sel] if sel < 4 else 0
            st.alu_a = ra
            res = alu8(st.alu_a, st.alu_b, cw.alu_op)
            st.alu_y = res.y
            st.flag_z = res.zero
            st.flag_c = res.cout

        if cw.reg_we and sel < 4:
            if op == 0x02 and ph == 1:
                st.regs[sel] = st.bus_data & 0xFF
            else:
                st.regs[sel] = st.alu_y & 0xFF

        if cw.mem_wr:
            val = st.alu_y if cw.y_oe else st.regs[0]
            addr = st.eff_addr if st.eff_addr else (st.operand & 0xFFFF)
            self.bus.write_cpu(addr, val)

        st.phase += 1

    def phases_done(self, phase_count: int) -> bool:
        return self.state.phase >= phase_count
