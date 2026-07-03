"""AND / OR / INV glue blocks."""

from __future__ import annotations

from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H, L, X


def _bin(a: int, b: int) -> int:
    if a == X or b == X:
        return X
    return H if (a & b) else L


def _bor(a: int, b: int) -> int:
    if a == X or b == X:
        return X
    return H if (a | b) else L


def _inv(a: int) -> int:
    if a == X:
        return X
    return H if a == L else L


class And2(Block):
  def eval_comb(self, ctx: SimContext) -> bool:
    out = _bin(ctx.get("a"), ctx.get("b"))
    return ctx.drive("y", out, self.name)


class Or2(Block):
  def eval_comb(self, ctx: SimContext) -> bool:
    out = _bor(ctx.get("a"), ctx.get("b"))
    return ctx.drive("y", out, self.name)


class Inv(Block):
  def eval_comb(self, ctx: SimContext) -> bool:
    return ctx.drive("y", _inv(ctx.get("a")), self.name)
