#!/usr/bin/env python3
"""Assemble and run fib_to_200 on plover_vm."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from macroasm import assemble, write_hex
from plover_vm.machine import PloverMachine

LIMIT = 200


def main() -> None:
    asm = (ROOT / "hw" / "fixtures" / "sw" / "fib_to_200.asm").read_text(encoding="utf-8")
    prog = assemble(asm)
    out = ROOT / "hw" / "fixtures" / "sram" / "fib_to_200.sram.hex"
    write_hex(prog, out)

    m = PloverMachine(engine="fast")
    m.load_cw(ROOT / "hw" / "fixtures" / "control" / "cw.hex")
    m.load_ram_program(out, 0)
    m.bus.ram.write(0x20, 0)
    m.bus.ram.write(0x21, 1)
    m.bus.map_mode = 1
    m.fast.pc = 0

    trace: list[int] = [0, 1]
    steps = 0
    while not m.halted and steps < 50_000:
        r1_before = m.fast.regs[1]
        m.step_once()
        steps += 1
        r1 = m.fast.regs[1]
        if r1 != r1_before and r1 not in trace:
            trace.append(r1)

    snap = m.snapshot()
    print("Fibonacci terms up to 200:")
    print(trace)
    print(f"Last term <= {LIMIT}: {snap.regs[1]}")
    print(f"Steps: {steps}, halted: {snap.halted}")
    print(json.dumps({"regs": snap.regs, "trace": trace}, indent=2))

    assert snap.halted
    assert snap.regs[1] == 144
    assert 144 in trace and trace[-1] == 144


if __name__ == "__main__":
    main()
