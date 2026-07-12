#!/usr/bin/env python3
"""Desk cycle model: Gi1 multiphase vs FE1 vs FE2 (primitive one-clock study).

stdlib only. Non-normative research estimates.
FE1 costs are structural minima assuming impossible bus overlap is still
counted as 1 only for the optimistic column — see fe1_possible flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


F_SYS_HZ = 2_000_000


@dataclass(frozen=True)
class OpCost:
    name: str
    """Gi1: fetch bytes approximated as separate SYS (1 per byte) + exec phases."""
    gi1_fetch_sys: int
    gi1_exec_sys: int
    """FE1: claimed single SYS if fe1_possible else same as structural lower bound note."""
    fe1_sys: int
    fe1_possible: bool
    """FE2: fetch slots + execute slots (no idle)."""
    fe2_fetch_sys: int
    fe2_exec_sys: int

    @property
    def gi1_total(self) -> int:
        return self.gi1_fetch_sys + self.gi1_exec_sys

    @property
    def fe2_total(self) -> int:
        return self.fe2_fetch_sys + self.fe2_exec_sys


# FE2 drops ADD/CMP idle (exec 3->1). MEM/BEQ packed optimistically (E=1);
# CALL E=3 / RET E=2. Lab fail @ low clock => stretch E (see opcode-fe-table.md).
OPS: dict[str, OpCost] = {
    "ADD": OpCost("ADD", 2, 3, 1, False, 2, 1),
    "CMP": OpCost("CMP", 2, 3, 1, False, 2, 1),
    "LDA": OpCost("LDA", 2, 2, 1, False, 2, 1),
    "STA": OpCost("STA", 2, 2, 1, False, 2, 1),
    "BEQ": OpCost("BEQ", 3, 2, 1, False, 3, 1),
    "JMP": OpCost("JMP", 3, 1, 1, False, 3, 1),
    "CALL": OpCost("CALL", 3, 1 + 4, 1, False, 3, 3),
    "RET": OpCost("RET", 1, 1 + 3, 1, False, 1, 2),
}


@dataclass(frozen=True)
class RunResult:
    label: str
    macros: int
    sys_cycles: int
    macros_per_s: float
    ipc: float


def total_sys(program: Iterable[str], mode: str) -> tuple[int, int]:
    """Return (macro_count, sys_cycles). mode: gi1 | fe1 | fe2."""
    n = 0
    cycles = 0
    for name in program:
        op = OPS[name]
        n += 1
        if mode == "gi1":
            cycles += op.gi1_total
        elif mode == "fe1":
            # Optimistic column: always fe1_sys, even when fe1_possible is False
            # (shows the number you wished for; SUMMARY treats as non-physical).
            cycles += op.fe1_sys
        elif mode == "fe2":
            cycles += op.fe2_total
        else:
            raise ValueError(mode)
    return n, cycles


def evaluate(program: Iterable[str], mode: str, f_sys_hz: int = F_SYS_HZ) -> RunResult:
    prog = list(program)
    n, cycles = total_sys(prog, mode)
    if n <= 0 or cycles <= 0:
        raise ValueError("empty")
    return RunResult(
        label=mode,
        macros=n,
        sys_cycles=cycles,
        macros_per_s=n * (f_sys_hz / cycles),
        ipc=n / cycles,
    )


def uplift_pct(base: RunResult, cand: RunResult) -> float:
    if base.macros_per_s <= 0:
        return 0.0
    return 100.0 * (cand.macros_per_s - base.macros_per_s) / base.macros_per_s


MIX_BALANCED = ["ADD", "LDA", "ADD", "CMP", "STA", "BEQ", "ADD", "JMP"]
MIX_ALU = ["ADD"] * 10
MIX_MEM = ["LDA", "STA"] * 5


def main() -> None:
    print(f"F_SYS = {F_SYS_HZ / 1e6:.1f} MHz")
    print("modes: gi1 (fetch+exec), fe1 (wishful 1), fe2 (F+E no idle)\n")
    for name, mix in [
        ("ADD×10", MIX_ALU),
        ("MEM×5 pairs", MIX_MEM),
        ("balanced", MIX_BALANCED),
    ]:
        g = evaluate(mix, "gi1")
        f1 = evaluate(mix, "fe1")
        f2 = evaluate(mix, "fe2")
        print(f"=== {name} ===")
        for r, tag in ((g, "gi1"), (f1, "fe1*"), (f2, "fe2")):
            extra = ""
            if tag.startswith("fe1"):
                extra = f"  uplift_vs_gi1={uplift_pct(g, r):+.1f}%  (*non-physical if fe1_possible=False)"
            elif tag == "fe2":
                extra = f"  uplift_vs_gi1={uplift_pct(g, r):+.1f}%"
            print(
                f"  {tag:6s}  macros={r.macros:3d}  sys={r.sys_cycles:4d}  "
                f"IPC={r.ipc:.3f}  rate={r.macros_per_s / 1e6:.3f} M/s{extra}"
            )
        print()
    print("Per-op fe1_possible:")
    for k, op in OPS.items():
        print(f"  {k:6s}  FE1_possible={op.fe1_possible}  gi1={op.gi1_total}  fe2={op.fe2_total}")


if __name__ == "__main__":
    main()
