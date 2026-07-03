"""3×8 GPR regfile — async R0->A, R1->B."""

from __future__ import annotations

from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H, L


class GprRegfile(Block):
    def __init__(self, name: str = "gpr") -> None:
        super().__init__(name)
        self.regs = [0, 0, 0]

    def qa(self) -> int:
        return self.regs[0] & 0xFF

    def qb(self) -> int:
        return self.regs[1] & 0xFF

    def read(self, sel: int) -> int:
        return self.regs[sel & 3] & 0xFF if sel < 3 else 0

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        qa, qb = self.qa(), self.qb()
        for i in range(8):
            changed |= ctx.drive(f"net_a{i}", (qa >> i) & 1, self.name)
            changed |= ctx.drive(f"net_b{i}", (qb >> i) & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if (ctx.get("net_reg_we") & 1) != H:
            return
        w_sel = (ctx.get("net_w_sel0") & 1) | ((ctx.get("net_w_sel1") & 1) << 1)
        if w_sel > 2:
            return
        din = sum((ctx.get(f"net_d{i}") & 1) << i for i in range(8))
        self.regs[w_sel] = din & 0xFF
