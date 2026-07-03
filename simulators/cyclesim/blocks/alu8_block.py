"""ALU8 SimContext block — drives Y and flags from A/B operands."""

from __future__ import annotations

from simulators.cyclesim.blocks.alu8 import Alu8
from simulators.cyclesim.engine import Block, SimContext


class Alu8Block(Block):
    def __init__(self, name: str = "alu8_blk") -> None:
        super().__init__(name)
        self.alu = Alu8(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        a = sum((ctx.get(f"net_a{i}") & 1) << i for i in range(8))
        b = sum((ctx.get(f"net_b{i}") & 1) << i for i in range(8))
        ctrl = self.alu.read_ctrl(ctx)
        res = self.alu.eval(ctx, a, b)
        self.alu.drive_outputs(ctx, res)
        changed = False
        if ctx.get("net_y_oe") & 1:
            # MEM_ST ph0: R0 on q_a — NOP ALU Y is 0; pass A operand to D bus.
            out = a if res.y == 0 and ctrl.cin == 0 and ctrl.bctrl == 0 else res.y
            for i in range(8):
                changed |= ctx.drive(f"net_d{i}", (out >> i) & 1, self.name)
        return changed
