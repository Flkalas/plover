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
    assert runner.gpr[1] == 0  # ADD $00 ph1 latched imm8 to R1
    assert runner.gpr[2] == 0x42


def test_add_zero_after_cmp_latches_r1() -> None:
    """ALU_REG ph1: REG_WE always latches imm8 to R1 (mandatory per cpld-system-controller §7)."""
    runner = ProgramRunner()
    runner.load_rom_bytes(
        bytes([0x02, 0x10, 0x0D, 0xE9, 0x01, 0x00, 0x0A]),
        base=0,
    )
    runner.load_ram(0x10, 0x10)
    runner.reset(pc=0)
    runner.run_until_halt(max_steps=200)
    assert runner.halted
    assert runner.gpr[0] == 0x10
    assert runner.gpr[1] == 0
    assert runner.gpr[2] == 0x10


def test_tfr20() -> None:
    runner = ProgramRunner()
    runner.load_rom_bytes(bytes([0x18, 0x0A]), base=0)  # TFR20; HALT
    runner.reset(pc=0)
    runner.cpu.gpr.regs[0] = 0xAB
    runner.run_until_halt(max_steps=50)
    assert runner.gpr[2] == 0xAB


def test_fib_upto_250() -> None:
    """Largest Fibonacci term <= 250 is 233 (stops before 8-bit overflow on next step)."""
    from simulators.cyclesim.fixtures.rom_builder import (
        ADDR_FIB_A,
        ADDR_FIB_B,
        FIB_LIMIT,
        build_fib_to_limit_rom,
        fib_pair_before_target,
        last_fib_leq,
    )

    rom, ram_init, target = build_fib_to_limit_rom(FIB_LIMIT)
    assert target == 233
    exp_a, exp_b = fib_pair_before_target(FIB_LIMIT)
    assert exp_b == target

    runner = ProgramRunner()
    runner.load_rom_bytes(rom, base=0)
    for addr, val in ram_init.items():
        runner.load_ram(addr, val)
    runner.reset(pc=0)
    steps = runner.run_until_halt(max_steps=2_000)
    assert runner.halted, f"did not halt in {steps} steps"
    exp_max, _exp_next = last_fib_leq(FIB_LIMIT)
    assert exp_max == 233
    assert runner.gpr[0] == exp_max
    assert runner.gpr[1] == exp_max
    assert runner.cpu.mem.read(ADDR_FIB_A) == exp_a
    assert runner.cpu.mem.read(ADDR_FIB_B) == exp_max

