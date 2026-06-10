"""Sequential models — 574 GPR, clock edges (logic from hw.logic.gates)."""

from __future__ import annotations

from cyclesim.models.base import CycleModel, L
from hw.logic import gates


class Regfile574Gpr(CycleModel):
    """4×8-bit GPR — comb read QA/QB, write on CP ↑ when REG_WE and LOAD_R*."""

    part = "REGFILE_574_GPR"
    is_sequential = True

    def __init__(self, ref: str, pin_nets: dict[str, str], ctx) -> None:
        super().__init__(ref, pin_nets, ctx)
        self._regs = [0, 0, 0, 0]
        self._prev_clk = L

    def set_gpr(self, index: int, value: int) -> None:
        self._regs[index & 3] = value & 0xFF

    def get_gpr(self, index: int) -> int:
        return self._regs[index & 3]

    def eval_comb(self) -> bool:
        return self._read_out()

    def eval_clock(self, edge: str) -> bool:
        if edge != "posedge":
            return False
        clk = self.read_bit("CLK")
        if self._prev_clk == L and clk == 1:
            updated = gates.regfile_maybe_write(
                self._regs,
                self.read_bit,
                lambda p: p in self.pin_nets,
            )
            if updated is not None:
                self._regs = updated
        self._prev_clk = clk
        return self._read_out()

    def _read_out(self) -> bool:
        qa, qb = gates.regfile_read_ports(self._regs, self.read_bit)
        changed = False
        for i in range(8):
            changed |= self.ctx.drive_net(self.net_for(f"QA{i}"), (qa >> i) & 1, self.ref)
            changed |= self.ctx.drive_net(self.net_for(f"QB{i}"), (qb >> i) & 1, self.ref)
        return changed


class CpldRegfile(CycleModel):
    """4×8-bit GPR inside CPLD — comb read, write on CP ↑ when WE."""

    part = "CPLD_REGFILE"
    is_sequential = True

    def __init__(self, ref: str, pin_nets: dict[str, str], ctx) -> None:
        super().__init__(ref, pin_nets, ctx)
        self._regs = [0, 0, 0, 0]
        self._prev_clk = L

    def set_gpr(self, index: int, value: int) -> None:
        self._regs[index & 3] = value & 0xFF

    def get_gpr(self, index: int) -> int:
        return self._regs[index & 3]

    def eval_comb(self) -> bool:
        return self._read_out()

    def eval_clock(self, edge: str) -> bool:
        if edge != "posedge":
            return False
        clk = self.read_bit("CLK")
        if self._prev_clk == L and clk == 1 and self.read_bit("WE") == 1:
            w_sel = self.read_bit("W_SEL0") | (self.read_bit("W_SEL1") << 1)
            d = sum(self.read_bit(f"D{i}") << i for i in range(8))
            self._regs[w_sel & 3] = d & 0xFF
        self._prev_clk = clk
        return self._read_out()

    def _read_out(self) -> bool:
        ra = self.read_bit("R_SEL_A0") | (self.read_bit("R_SEL_A1") << 1)
        rb = self.read_bit("R_SEL_B0") | (self.read_bit("R_SEL_B1") << 1)
        qa = self._regs[ra & 3]
        qb = self._regs[rb & 3]
        changed = False
        for i in range(8):
            changed |= self.ctx.drive_net(self.net_for(f"QA{i}"), (qa >> i) & 1, self.ref)
            changed |= self.ctx.drive_net(self.net_for(f"QB{i}"), (qb >> i) & 1, self.ref)
        return changed
