"""CPLD-DP — R0 (AC) only (Gi1 v1.0)."""

from __future__ import annotations

from simulators.cyclesim.blocks.cpld.gic import NET_GIC_REG_WE
from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H


class CpldDp(Block):
    """Single GPR R0; q_a to ALU A; ALU B from net_mbr (MBR 574)."""

    def __init__(self, name: str = "cpld_dp") -> None:
        super().__init__(name)
        self.regs = [0, 0, 0]  # [R0, _, _] — R1/R2 slots unused (test compat)

    def qa(self) -> int:
        return self.regs[0] & 0xFF

    def qb(self) -> int:
        """Legacy alias — Gi1 ALU B is not from CPLD."""
        return 0

    def read(self, sel: int) -> int:
        if sel == 0:
            return self.qa()
        return 0

    def _d_in(self, ctx: SimContext) -> int:
        return sum((ctx.get(f"net_d{i}") & 1) << i for i in range(8))

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        qa = self.qa()
        for i in range(8):
            changed |= ctx.drive(f"net_a{i}", (qa >> i) & 1, self.name)
            # Gi1: ALU B operand from MBR hold (net_mbr* driven by MbrReg)
            changed |= ctx.drive(f"net_b{i}", ctx.get(f"net_mbr{i}") & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if (ctx.get(NET_GIC_REG_WE) & 1) != H:
            return
        self.regs[0] = self._d_in(ctx) & 0xFF

    def apply_g_ic(self, ctx: SimContext) -> None:
        """One-shot write for unit tests (no clock)."""
        self.tick(ctx)
