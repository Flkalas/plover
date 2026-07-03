"""CLI entry: python -m simulators.cyclesim"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from simulators.cyclesim.program import ProgramRunner

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def cmd_run(args: argparse.Namespace) -> int:
    runner = ProgramRunner()
    hex_path = Path(args.rom)
    if not hex_path.is_file():
        hex_path = FIXTURES / args.rom
    runner.load_rom_hex(hex_path, base=args.base)
    if args.ram_init:
        for pair in args.ram_init.split(","):
            addr_s, val_s = pair.split("=")
            runner.load_ram(int(addr_s, 0), int(val_s, 0))
    runner.reset(pc=args.pc)
    steps = runner.run_until_halt(max_steps=args.max_steps)
    print(f"steps={steps} halted={runner.halted} pc=0x{runner.pc:04X}")
    print(f"gpr R0=0x{runner.gpr[0]:02X} R1=0x{runner.gpr[1]:02X} R2=0x{runner.gpr[2]:02X}")
    return 0 if runner.halted else 1


def cmd_test(_: argparse.Namespace) -> int:
    import pytest

    tests = Path(__file__).resolve().parent / "tests"
    return pytest.main([str(tests), "-q"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simulators.cyclesim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run ROM program until HALT")
    run_p.add_argument("rom", help="ROM hex file or fixture name")
    run_p.add_argument("--pc", type=lambda x: int(x, 0), default=0)
    run_p.add_argument("--base", type=lambda x: int(x, 0), default=0)
    run_p.add_argument("--max-steps", type=int, default=500)
    run_p.add_argument("--ram-init", default="", help="addr=val,... e.g. 0x42=0x42")
    run_p.set_defaults(func=cmd_run)

    test_p = sub.add_parser("test", help="Run pytest suite")
    test_p.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
