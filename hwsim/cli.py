"""CLI entry points for hwsim."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hwsim.export_svg import export_svg
from hwsim.kicad_diff import diff_kicad
from hwsim.netlist import load_netlist, validate_netlist
from hwsim.report import write_report
from hwsim.serve import serve
from hwsim.simulator import run_test


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def cmd_validate(args: argparse.Namespace) -> int:
    root = repo_root()
    path = Path(args.netlist)
    if not path.is_absolute():
        path = root / path
    nl = load_netlist(path)
    errors = validate_netlist(nl, root)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: {path} block={nl.block} instances={len(nl.instances)} nets={len(nl.nets)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    root = repo_root()
    tests_dir = root / "hw" / "tests"
    if args.all:
        tests = sorted(tests_dir.glob("*.yaml"))
    else:
        tests = [Path(args.test)]
    if not tests:
        print("No tests found", file=sys.stderr)
        return 1

    failed = 0
    for tp in tests:
        if not tp.is_absolute():
            tp = root / tp if (root / tp).exists() else tests_dir / tp.name
        if not tp.is_file():
            print(f"Missing test {tp}", file=sys.stderr)
            failed += 1
            continue
        result = run_test(tp, root)
        out_dir = root / "build" / "hwsim" / result["test"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (out_dir / "waves.json").write_text(json.dumps(result["waves"], indent=2), encoding="utf-8")
        write_report(out_dir, result)
        nl_path = _netlist_for_test(tp, root)
        if nl_path:
            svg = export_svg(load_netlist(nl_path))
            (out_dir / "wiring.svg").write_text(svg, encoding="utf-8")
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {result['test']}")
        if result["errors"]:
            for e in result["errors"]:
                print(f"  {e}")
        if not result["passed"]:
            failed += 1
    return 1 if failed else 0


def _netlist_for_test(test_path: Path, root: Path) -> Path | None:
    from hwsim import yaml_util
    data = yaml_util.load_file(str(test_path))
    if not isinstance(data, dict):
        return None
    rel = data.get("netlist")
    if not rel:
        return None
    p = (test_path.parent / rel).resolve()
    if p.is_file():
        return p
    p2 = (root / rel).resolve()
    return p2 if p2.is_file() else None


def cmd_report(args: argparse.Namespace) -> int:
    root = repo_root()
    build = Path(args.build_dir)
    if not build.is_absolute():
        build = root / build
    result_path = build / "result.json"
    if not result_path.is_file():
        print(f"No result.json in {build}", file=sys.stderr)
        return 1
    result = json.loads(result_path.read_text(encoding="utf-8"))
    write_report(build, result)
    print(f"Report written to {build / 'report.html'}")
    return 0


def cmd_export_svg(args: argparse.Namespace) -> int:
    root = repo_root()
    path = Path(args.netlist)
    if not path.is_absolute():
        path = root / path
    nl = load_netlist(path)
    svg = export_svg(nl)
    out = Path(args.output) if args.output else path.with_suffix(".svg")
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


def cmd_diff_kicad(args: argparse.Namespace) -> int:
    root = repo_root()
    kicad = Path(args.kicad_net)
    yaml_nl = Path(args.netlist)
    if not kicad.is_absolute():
        kicad = root / kicad
    if not yaml_nl.is_absolute():
        yaml_nl = root / yaml_nl
    mismatches = diff_kicad(kicad, yaml_nl)
    if mismatches:
        for m in mismatches:
            print(f"MISMATCH: {m}")
        return 1
    print("OK: KiCad netlist matches YAML")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hwsim", description="Plover electrical timing simulator")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="Validate netlist YAML")
    v.add_argument("netlist")
    v.set_defaults(func=cmd_validate)

    r = sub.add_parser("run", help="Run timing test(s)")
    r.add_argument("test", nargs="?", help="Test YAML path")
    r.add_argument("--all", action="store_true", help="Run all hw/tests/*.yaml")
    r.set_defaults(func=cmd_run)

    rep = sub.add_parser("report", help="Regenerate HTML report from build dir")
    rep.add_argument("build_dir")
    rep.set_defaults(func=cmd_report)

    ex = sub.add_parser("export-svg", help="Export wiring SVG from netlist")
    ex.add_argument("netlist")
    ex.add_argument("-o", "--output", default="")
    ex.set_defaults(func=cmd_export_svg)

    d = sub.add_parser("diff-kicad", help="Compare KiCad netlist to YAML")
    d.add_argument("kicad_net")
    d.add_argument("netlist")
    d.set_defaults(func=cmd_diff_kicad)

    s = sub.add_parser("serve", help="Phase1 p1-viewer local server")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_serve)

    return p


def cmd_serve(args: argparse.Namespace) -> int:
    serve(host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
