#!/usr/bin/env python3
"""CPLD control-extraction Pareto search — GPR in CPLD, control in 74HC/Flash."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cpld_ctrl_arch import (  # noqa: E402
    ARCH_BASELINE_FSM,
    CONTROL_ARCHITECTURES,
    IndexWidth,
    min_dip,
    pareto_front,
    score_all_configs,
    score_control_arch,
)
from cpld_ctrl_model import active_idx5_slots, build_v10_ctrl_table  # noqa: E402

BUILD_DIR = ROOT / "build"
OUT_JSON = BUILD_DIR / "cpld_ctrl_pareto.json"


def run_search(
    arches: tuple[str, ...] = CONTROL_ARCHITECTURES,
    *,
    cap: int = 50,
) -> dict:
    all_costs = score_all_configs(arches)
    front = pareto_front(all_costs)
    if len(front) > cap:
        front = front[:cap]

    baseline = score_control_arch(ARCH_BASELINE_FSM, IndexWidth.IDX5)
    min_pure = min_dip(all_costs, pure_only=True)
    min_any = min_dip(all_costs, pure_only=False)

    rows = build_v10_ctrl_table()
    return {
        "baseline": baseline.as_dict(),
        "min_dip_pure_74hc": min_pure.as_dict() if min_pure else None,
        "min_dip_any": min_any.as_dict() if min_any else None,
        "ctrl_rows": len(rows),
        "idx5_slots_used": len(active_idx5_slots(rows)),
        "pareto_front": [c.as_dict() for c in front],
        "all_configs": [c.as_dict() for c in all_costs],
        "total_configs": len(all_costs),
        "feasible_count": sum(1 for c in all_costs if c.feasible),
        "pareto_count": len(front),
    }


def print_report(data: dict) -> None:
    print("CPLD control extraction Pareto search (GPR in CPLD)")
    print(f"  ctrl rows: {data['ctrl_rows']}  idx5 slots: {data['idx5_slots_used']}")
    print(f"  configs: {data['total_configs']}  feasible: {data['feasible_count']}")
    print()

    def row(label: str, d: dict | None) -> None:
        if d is None:
            print(f"  {label:<18} (none)")
            return
        print(
            f"  {label:<18} DIP={d['dip_74hc']:>3}  delay={d['delay_max_ns']:>3}ns  "
            f"flash={d['flash_rows']:>3}  MC={d['cpld_mc']:>2}  hops={d['wire_hops']:>3}  "
            f"gates={d['gates']:>4}  {'OK' if d['feasible'] else 'NO'}"
        )
        print(f"    {d['key']}")

    print("Corners:")
    row("baseline", data["baseline"])
    row("min DIP (74HC)", data["min_dip_pure_74hc"])
    row("min DIP (any)", data["min_dip_any"])
    print()

    b = data["baseline"]
    if data["min_dip_any"]:
        m = data["min_dip_any"]
        print(
            f"  vs baseline: DIP delta {m['dip_74hc'] - b['dip_74hc']:+d}, "
            f"MC delta {m['cpld_mc'] - b['cpld_mc']:+d}, "
            f"flash +{m['flash_rows']}"
        )
    print()

    print("Pareto front (dip, delay, flash_rows):")
    hdr = f"  {'DIP':>3} {'delay':>5} {'flash':>5} {'MC':>3} {'gates':>5}  key"
    print(hdr)
    for d in data["pareto_front"]:
        print(
            f"  {d['dip_74hc']:>3} {d['delay_max_ns']:>5} {d['flash_rows']:>5} "
            f"{d['cpld_mc']:>3} {d['gates']:>5}  {d['key']}"
        )


def parse_arches(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return CONTROL_ARCHITECTURES
    names = tuple(s.strip() for s in raw.split(",") if s.strip())
    for n in names:
        if n not in CONTROL_ARCHITECTURES:
            raise SystemExit(f"unknown arch: {n!r} (choose from {CONTROL_ARCHITECTURES})")
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="CPLD control extraction architecture search")
    ap.add_argument("--pareto", action="store_true", help="Print Pareto report")
    ap.add_argument("--json", type=Path, nargs="?", const=OUT_JSON, metavar="PATH")
    ap.add_argument("--arch", type=str, help="Comma-separated arch subset")
    ap.add_argument("--top", type=int, default=50, help="Max Pareto entries")
    args = ap.parse_args()

    arches = parse_arches(args.arch)
    data = run_search(arches, cap=args.top)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json}")

    if args.pareto or not args.json:
        print_report(data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
