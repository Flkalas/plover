#!/usr/bin/env python3
"""Assemble and run 16-bit fib_to_20000 on plover_vm."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from macroasm import assemble, write_hex
from plover_vm.machine import PloverMachine

LIMIT = 20_000
EXPECTED_LAST = 17_711  # largest Fibonacci <= 20000


def fib_upto(limit: int) -> list[int]:
    a, b = 0, 1
    seq = [a, b]
    while True:
        n = a + b
        if n > limit:
            break
        seq.append(n)
        a, b = b, n
    return seq


def main() -> None:
    asm = (ROOT / "hw" / "fixtures" / "sw" / "fib_to_20000.asm").read_text(encoding="utf-8")
    prog = assemble(asm)
    out = ROOT / "hw" / "fixtures" / "sram" / "fib_to_20000.sram.hex"
    write_hex(prog, out)

    m = PloverMachine(engine="fast")
    m.bus.map_mode = 1
    m.load_ram_program(out, 0)
    m.fast.regs16 = [0, 1, 0, 0]
    m.fast.pc = 0

    ref = fib_upto(LIMIT)
    seen: list[int] = [0, 1]
    steps = 0
    while not m.halted and steps < 500_000:
        w1 = m.fast.regs16[1]
        m.step_once()
        steps += 1
        w1_after = m.fast.regs16[1]
        if w1_after != w1 and w1_after not in seen:
            seen.append(w1_after)

    snap = m.fast.regs16
    print(f"Fibonacci (16-bit) last term <= {LIMIT}: {snap[1]} (0x{snap[1]:04X})")
    print(f"Reference sequence tail: ... {ref[-4:]}")
    print(f"Steps: {steps}, halted: {m.halted}")
    print(f"W regs: {[f'0x{v:04X}' for v in snap]}")
    print(json.dumps({"w1": snap[1], "w2": snap[2], "steps": steps}, indent=2))

    assert m.halted, "program did not halt"
    assert snap[1] == EXPECTED_LAST, f"expected {EXPECTED_LAST}, got {snap[1]}"
    assert snap[2] == 28_657, "W2 should hold first term > 20000 (28657)"


if __name__ == "__main__":
    main()
