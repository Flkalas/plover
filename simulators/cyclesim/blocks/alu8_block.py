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
        res = self.alu.eval(ctx, a, b)
        self.alu.drive_outputs(ctx, res)
        changed = False
        if ctx.get("net_y_oe") & 1:
            for i in range(8):
                changed |= ctx.drive(f"net_d{i}", (res.y >> i) & 1, self.name)
        return changed
