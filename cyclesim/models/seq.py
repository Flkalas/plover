"""Sequential models — 574 GPR, clock edges."""

from __future__ import annotations

from cyclesim.models.base import CycleModel, L, Z


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
            self._maybe_write()
        self._prev_clk = clk
        return self._read_out()

    def _maybe_write(self) -> None:
        if self.read_bit("REG_WE") == 0:
            return
        val = sum(self.read_bit(f"D{i}") << i for i in range(8))
        for r in range(4):
            pin = f"LOAD_R{r}"
            if pin in self.pin_nets and self.read_bit(pin):
                self._regs[r] = val & 0xFF
                return

    def _sel(self, prefix: str) -> int:
        return self.read_bit(f"{prefix}0") | (self.read_bit(f"{prefix}1") << 1)

    def _read_out(self) -> bool:
        ra = self._sel("RA") & 3
        rb = self._sel("RB") & 3
        qa, qb = self._regs[ra], self._regs[rb]
        changed = False
        for i in range(8):
            changed |= self.ctx.drive_net(self.net_for(f"QA{i}"), (qa >> i) & 1, self.ref)
            changed |= self.ctx.drive_net(self.net_for(f"QB{i}"), (qb >> i) & 1, self.ref)
        return changed
