#!/usr/bin/env python3
"""4-axis CPU architecture Pareto search ??build/cpu_arch_pareto.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cpu_arch_model import (  # noqa: E402
    baseline_v10_config,
    corner_h1_config,
    corner_h2_config,
    iter_configs,
    pareto_front,
    score_config,
)

BUILD_DIR = ROOT / "build"
OUT_JSON = BUILD_DIR / "cpu_arch_pareto.json"


def run_search(*, cap: int = 50) -> dict:
    all_costs = [score_config(c) for c in iter_configs()]
    front = pareto_front(all_costs)
    if len(front) > cap:
        front = front[:cap]

    baseline = score_config(baseline_v10_config())
    h1 = score_config(corner_h1_config())
    h2 = score_config(corner_h2_config())

    return {
        "baseline_v10": baseline.as_dict(),
        "corner_h1": h1.as_dict(),
        "corner_h2": h2.as_dict(),
        "pareto_front": [c.as_dict() for c in front],
        "total_configs": len(all_costs),
        "feasible_count": sum(1 for c in all_costs if c.feasible),
        "pareto_count": len(front),
    }


def print_report(data: dict) -> None:
    print("CPU 4-axis architecture Pareto search")
    print(f"  configs scored: {data['total_configs']}  feasible: {data['feasible_count']}")
    print()

    def row(label: str, d: dict) -> None:
        print(
            f"  {label:<14} DIP={d['dip_74hc']:>2}  delay={d['delay_max_ns']:>3}ns  "
            f"flash={d['flash_rows']:>4}  MC={d['cpld_mc']:>2}  hops={d['wire_hops']:>3}  "
            f"{'OK' if d['feasible'] else 'NO'}"
        )
        print(f"    {d['key']}")

    print("Corners:")
    row("baseline", data["baseline_v10"])
    row("H1 hybrid", data["corner_h1"])
    row("H2 cw16", data["corner_h2"])
    print()

    b = data["baseline_v10"]
    dip_delta = b["dip_74hc"] - min(
        data["corner_h1"]["dip_74hc"],
        data["corner_h2"]["dip_74hc"],
    )
    delay_delta = b["delay_max_ns"] - min(
        data["corner_h1"]["delay_max_ns"],
        data["corner_h2"]["delay_max_ns"],
    )
    print(f"  vs baseline: DIP savings up to {dip_delta}, delay improvement up to {delay_delta} ns")
    print()

    print("Pareto front (dip, delay, flash_rows):")
    hdr = f"  {'DIP':>3} {'delay':>5} {'flash':>5} {'MC':>3} {'hops':>4}  key"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for d in data["pareto_front"][:20]:
        print(
            f"  {d['dip_74hc']:>3} {d['delay_max_ns']:>5} {d['flash_rows']:>5} "
            f"{d['cpld_mc']:>3} {d['wire_hops']:>4}  {d['key']}"
        )
    if data["pareto_count"] > 20:
        print(f"  ... +{data['pareto_count'] - 20} more in JSON")


def main() -> None:
    parser = argparse.ArgumentParser(description="CPU 4-axis Pareto architecture search")
    parser.add_argument("--pareto", action="store_true", help="Run search and write JSON")
    parser.add_argument("--json-only", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--cap", type=int, default=50, help="Max Pareto entries")
    args = parser.parse_args()

    if not args.pareto and not args.json_only:
        parser.print_help()
        return

    data = run_search(cap=args.cap)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if args.json_only:
        print(json.dumps(data, indent=2))
    else:
        print_report(data)
        print()
        print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
