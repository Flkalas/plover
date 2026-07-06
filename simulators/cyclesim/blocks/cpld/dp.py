"""CPLD-DP — GPR + TFR src mux (rev G)."""

from __future__ import annotations

from simulators.cyclesim.blocks.cpld.gic import (
    NET_GIC_REG_WE,
    NET_GIC_SRC0,
    NET_GIC_SRC1,
    NET_GIC_TFR_VALID,
    NET_GIC_W_SEL0,
    NET_GIC_W_SEL1,
)
from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H


class CpldDp(Block):
    """3×8 GPR on DP; async R0→A, R1→B; write from bus or TFR mux via G-IC."""

    def __init__(self, name: str = "cpld_dp") -> None:
        super().__init__(name)
        self.regs = [0, 0, 0]

    def qa(self) -> int:
        return self.regs[0] & 0xFF

    def qb(self) -> int:
        return self.regs[1] & 0xFF

    def read(self, sel: int) -> int:
        return self.regs[sel & 3] & 0xFF if sel < 3 else 0

    def _tfr_mux_data(self, ctx: SimContext) -> int:
        src = (ctx.get(NET_GIC_SRC0) & 1) | ((ctx.get(NET_GIC_SRC1) & 1) << 1)
        return self.read(src)

    def _d_in(self, ctx: SimContext) -> int:
        return sum((ctx.get(f"net_d{i}") & 1) << i for i in range(8))

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        qa, qb = self.qa(), self.qb()
        for i in range(8):
            changed |= ctx.drive(f"net_a{i}", (qa >> i) & 1, self.name)
            changed |= ctx.drive(f"net_b{i}", (qb >> i) & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if (ctx.get(NET_GIC_REG_WE) & 1) != H:
            return
        w_sel = (ctx.get(NET_GIC_W_SEL0) & 1) | ((ctx.get(NET_GIC_W_SEL1) & 1) << 1)
        if w_sel > 2:
            return
        if ctx.get(NET_GIC_TFR_VALID) & 1:
            data = self._tfr_mux_data(ctx)
        else:
            data = self._d_in(ctx)
        self.regs[w_sel] = data & 0xFF

    def apply_g_ic(self, ctx: SimContext) -> None:
        """One-shot write for unit tests (no clock)."""
        self.tick(ctx)
