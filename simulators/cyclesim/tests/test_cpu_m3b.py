"""M3b fetch + execute — mini program."""

from __future__ import annotations

from pathlib import Path

import pytest

from simulators.cyclesim.program import ProgramRunner

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_fetch_ir_mbr() -> None:
    runner = ProgramRunner()
    runner.load_rom_bytes(bytes([0x02, 0x42, 0x0A]), base=0)
    runner.reset(pc=0)
    runner.cpu.step()  # fetch LDA
    assert runner.ir == 0x02
    assert runner.mbr == 0x42
    assert runner.pc == 2


def test_m3b_mini_program() -> None:
    runner = ProgramRunner()
    runner.load_rom_hex(FIXTURES / "m3b_mini.hex")
    runner.load_ram(0x42, 0x42)
    runner.reset(pc=0)
    steps = runner.run_until_halt(max_steps=300)
    assert runner.halted, f"did not halt in {steps} steps"
    assert runner.gpr[0] == 0x42
    assert runner.gpr[2] == 0x42


def test_tfr20() -> None:
    runner = ProgramRunner()
    runner.load_rom_bytes(bytes([0x14, 0x0A]), base=0)  # TFR20; HALT
    runner.reset(pc=0)
    runner.cpu.gpr.regs[0] = 0xAB
    runner.run_until_halt(max_steps=50)
    assert runner.gpr[2] == 0xAB


def test_fib_upto_250() -> None:
    """Largest Fibonacci term <= 250 is 233 (stops before 8-bit overflow on next step)."""
    from simulators.cyclesim.fixtures.rom_builder import (
        ADDR_FIB_B,
        FIB_LIMIT,
        build_fib_to_limit_rom,
        last_fib_leq,
    )

    rom, ram_init, target = build_fib_to_limit_rom(FIB_LIMIT)
    assert target == 233

    runner = ProgramRunner()
    runner.load_rom_bytes(rom, base=0)
    for addr, val in ram_init.items():
        runner.load_ram(addr, val)
    runner.reset(pc=0)
    steps = runner.run_until_halt(max_steps=2_000)
    assert runner.halted, f"did not halt in {steps} steps"
    exp_max, _exp_next = last_fib_leq(FIB_LIMIT)
    assert exp_max == 233
    assert runner.gpr[1] == exp_max
    assert runner.gpr[0] == exp_max  # LDA $81 for CMP left R0 at result
    assert runner.cpu.mem.read(ADDR_FIB_B) == exp_max

