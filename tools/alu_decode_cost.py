"""Score 4-bit alu_op ??control-net decode as 74HC04/08/32 SOP (same model as gen_alu_decode_netlist)."""
from __future__ import annotations

from dataclasses import dataclass


def op_bits(op: int) -> tuple[int, int, int, int]:
    return (op & 1, (op >> 1) & 1, (op >> 2) & 1, (op >> 3) & 1)


@dataclass(frozen=True)
class DecodeCost:
    n04: int
    n08: int
    n32: int

    @property
    def total(self) -> int:
        return self.n04 + self.n08 + self.n32

    def __str__(self) -> str:
        return f"{self.n04}x04 {self.n08}x08 {self.n32}x32 total={self.total}"


class _GateCounter:
  """Count gates for SOP decode without emitting netlist YAML."""

  def __init__(self) -> None:
      self.n04 = 0
      self.n08 = 0
      self.n32 = 0
      self._internal = 0

  def cost(self) -> DecodeCost:
      return DecodeCost(self.n04, self.n08, self.n32)

  def _new04(self) -> None:
      self.n04 += 1

  def _new08(self) -> None:
      self.n08 += 1

  def _new32(self) -> None:
      self.n32 += 1

  def _fresh(self) -> str:
      self._internal += 1
      return f"_t{self._internal}"

  def _literal(self, bit: int, val: int) -> str:
      if val == 1:
          return f"op{bit}"
      self._new04()
      return self._fresh()

  def _and(self, a: str, b: str) -> str:
      if a == "gnd" or b == "gnd":
          return "gnd"
      if a == "vcc":
          return b
      if b == "vcc":
          return a
      self._new08()
      return self._fresh()

  def _and_many(self, terms: list[str]) -> str:
      cur = terms[0]
      for t in terms[1:]:
          cur = self._and(cur, t)
      return cur

  def _or(self, a: str, b: str) -> str:
      if a == "gnd":
          return b
      if b == "gnd":
          return a
      self._new32()
      return self._fresh()

  def _or_many(self, terms: list[str]) -> str:
      cur = terms[0]
      for t in terms[1:]:
          cur = self._or(cur, t)
      return cur

  def _match_op(self, op: int) -> str:
      b0, b1, b2, b3 = op_bits(op)
      return self._and_many([self._literal(0, b0), self._literal(1, b1), self._literal(2, b2), self._literal(3, b3)])

  def _buf(self) -> None:
      self._new08()


def score_truth_table(
    rows: list[dict],
    outputs: list[str],
    *,
    cmp_op: int | None = None,
    include_b_const_hi: bool = False,
    include_cmp_n: bool = True,
) -> DecodeCost:
    """Score decode cost for a 16-row truth table keyed by ``op`` (0..15).

    Each row maps output net names to 0/1. Unused op slots should be NOP (all zeros).
    """
    by_op = {int(r["op"]): r for r in rows}
    if len(by_op) != 16:
        raise ValueError(f"expected 16 op rows, got {len(by_op)}")

    gc = _GateCounter()

    for sig in outputs:
        ops = [op for op in range(16) if int(by_op[op].get(sig, 0)) == 1]
        if ops:
            gc._or_many([gc._match_op(op) for op in ops])
            gc._buf()
        else:
            gc._buf()

    if include_b_const_hi:
        ops_hi = [op for op in range(16) if int(by_op[op].get("b_const_hi", 0)) == 1]
        if ops_hi:
            gc._or_many([gc._match_op(op) for op in ops_hi])
            gc._buf()
        else:
            gc._buf()
        for _ in range(7):
            gc._buf()

    if include_cmp_n:
        if cmp_op is None:
            raise ValueError("cmp_op required when include_cmp_n=True")
        gc._match_op(cmp_op)
        gc._new04()

    return gc.cost()
