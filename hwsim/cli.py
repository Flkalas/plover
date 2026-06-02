"""CLI entry points for hwsim."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hwsim.export_schematic import export_schematic_html, export_schematic_svg
from hwsim.export_svg import export_svg
from hwsim.kicad_diff import diff_kicad
from hwsim.pinout import format_pinout_table, list_parts, load_pinout
from hwsim.netlist import load_netlist, validate_netlist
from hwsim.report import write_report
from hwsim.simulator import run_test
from hwsim import yaml_util

# OSC / recurring clock netlists — not simulated (VM + scope on real hardware).
_CLOCK_NETLIST_MARKERS = ("b3_clock", "blocks/clock.yaml")


def _clock_test_blocked(test_path: Path) -> str | None:
    data = yaml_util.load_file(str(test_path))
    if not isinstance(data, dict):
        return None
    rel = str(data.get("netlist", ""))
    if any(m in rel for m in _CLOCK_NETLIST_MARKERS):
        return (
            "Clock/OSC hwsim is disabled (recurring toggle exhausts RAM). "
            "Use plover_vm for micro-phases; alu_b3_latch for one 574 CP edge; scope for B3c."
        )
    return None


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
        blocked = _clock_test_blocked(tp)
        if blocked:
            print(f"BLOCKED: {tp.stem} — {blocked}", file=sys.stderr)
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


def cmd_export_schematic(args: argparse.Namespace) -> int:
    root = repo_root()
    path = Path(args.netlist)
    if not path.is_absolute():
        path = root / path
    nl = load_netlist(path)
    cols = int(args.columns)
    assembly = nl.block == "alu8" and not args.logical
    if assembly and cols == 5:
        cols = 4
    svg = export_schematic_svg(nl, cols=cols, assembly=assembly)
    out_svg = Path(args.output) if args.output else path.with_suffix(".schematic.svg")
    if not out_svg.is_absolute():
        out_svg = root / out_svg
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(svg, encoding="utf-8")
    print(f"Wrote {out_svg}")
    if args.html:
        out_html = out_svg.with_suffix(".html")
        if out_html == out_svg:
            out_html = out_svg.parent / (out_svg.stem + ".html")
        title = f"Plover {nl.block} schematic (14 DIP assembly)"
        if args.logical:
            title = f"Plover {nl.block} schematic (logical)"
        out_html.write_text(export_schematic_html(svg, title=title), encoding="utf-8")
        print(f"Wrote {out_html}")
    return 0


def cmd_pinout(args: argparse.Namespace) -> int:
    if args.list_parts:
        for part in list_parts():
            print(part)
        return 0
    if not args.part:
        print("Usage: python -m hwsim pinout 74HC283 | --list", file=sys.stderr)
        return 1
    try:
        data = load_pinout(args.part)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    text = format_pinout_table(data).replace("\u2014", "-").replace("\u2013", "-")
    print(text)
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

    sc = sub.add_parser(
        "export-schematic",
        help="DIP package schematic SVG (pins + net wires)",
    )
    sc.add_argument("netlist")
    sc.add_argument("-o", "--output", default="")
    sc.add_argument("--columns", type=int, default=5, help="Package columns in layout")
    sc.add_argument(
        "--logical",
        action="store_true",
        help="hwsim logical packages (alu8: 22 boxes incl. slices + glue)",
    )
    sc.add_argument("--html", action="store_true", help="Also write zoomable HTML viewer")
    sc.set_defaults(func=cmd_export_schematic)

    po = sub.add_parser("pinout", help="Print DIP pin map from hw/pinout/")
    po.add_argument("part", nargs="?", help="e.g. 74HC283")
    po.add_argument("--list", dest="list_parts", action="store_true", help="List indexed parts")
    po.set_defaults(func=cmd_pinout)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
