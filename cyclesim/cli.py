"""CLI for cyclesim."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cyclesim.runner import run_test
from hwsim.netlist import load_netlist, validate_netlist

ROOT = Path(__file__).resolve().parents[1]


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.netlist)
    if not path.is_absolute():
        path = ROOT / path
    nl = load_netlist(path)
    errors = validate_netlist(nl, ROOT)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: {path} block={nl.block} instances={len(nl.instances)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    tests_dir = ROOT / "hw" / "tests" / "cyclesim"
    if args.all:
        tests = sorted(tests_dir.glob("*.yaml"))
    else:
        tp = Path(args.test)
        tests = [ROOT / tp if (ROOT / tp).exists() else tests_dir / tp.name]
    failed = 0
    for tp in tests:
        if not tp.is_file():
            print(f"Missing {tp}", file=sys.stderr)
            failed += 1
            continue
        result = run_test(tp, ROOT)
        out_dir = ROOT / "build" / "cyclesim" / result["test"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (out_dir / "waves.json").write_text(json.dumps(result["waves"], indent=2), encoding="utf-8")
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {result['test']}")
        for e in result["errors"]:
            print(f"  {e}")
        if not result["passed"]:
            failed += 1
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cyclesim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("netlist")
    v.set_defaults(func=cmd_validate)

    r = sub.add_parser("run")
    r.add_argument("test", nargs="?", default=None)
    r.add_argument("--all", action="store_true")
    r.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    if args.cmd == "run" and not args.all and not args.test:
        parser.error("run requires a test path or --all")
    return args.func(args)
