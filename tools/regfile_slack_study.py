"""Print 8 vs 4 register timing study from hwsim slack tests + analytical summary."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "hw" / "tests"
BUILD = ROOT / "build" / "hwsim"

BUDGET_NS = 250
MARGIN_NS = 15
ALU_ONLY_NS = 169  # alu_b3_sub_critical max corner
SETUP_574_NS = 8  # not counted on D0/CP slack hops — add for latch budget

TOPOLOGY_META = {
    "regfile_rmw_8x151": {
        "label": "8 reg · 8×151/port (single-stage 8:1)",
        "regs": 8,
        "mux_ic": 16,
        "574_extra": 8,
    },
    "regfile_rmw_4x153": {
        "label": "4 reg · 4×153/port (single-stage 4:1)",
        "regs": 4,
        "mux_ic": 8,
        "574_extra": 4,
    },
    "regfile_rmw_8x153157": {
        "label": "8 reg · 4×153+4×157/port (two-stage 8:1)",
        "regs": 8,
        "mux_ic": 24,
        "574_extra": 8,
    },
}


def _run_hwsim(test_name: str) -> dict:
    test_path = TESTS / f"{test_name}_slack.yaml"
    subprocess.run(
        [sys.executable, "-m", "hwsim", "run", str(test_path.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
    )
    return json.loads((BUILD / f"{test_name}_slack" / "result.json").read_text(encoding="utf-8"))


def _row(test_name: str, result: dict) -> dict:
    meta = TOPOLOGY_META[test_name]
    checks = result.get("checks", [])
    comb = next(c for c in checks if c["type"] == "slack" and "U_MUX" in str(c.get("path", [])))
    comb_delay = comb["delay_ns"]
    e2e_delay = comb_delay + SETUP_574_NS
    e2e_slack = BUDGET_NS - e2e_delay
    return {
        "name": test_name,
        "label": meta["label"],
        "regs": meta["regs"],
        "mux_ic": meta["mux_ic"],
        "574_extra": meta["574_extra"],
        "comb_delay_ns": comb_delay,
        "comb_slack_ns": comb["slack_ns"],
        "e2e_delay_ns": e2e_delay,
        "e2e_slack_ns": e2e_slack,
        "pass_15ns": e2e_slack >= MARGIN_NS,
        "passed": result["passed"] and e2e_slack >= 0,
    }


def main() -> None:
    gen = ROOT / "tools" / "gen_regfile_slack_test.py"
    subprocess.run([sys.executable, str(gen)], cwd=ROOT, check=True)

    rows = []
    for name in TOPOLOGY_META:
        result = _run_hwsim(name)
        rows.append(_row(name, result))

    print()
    print("=== Plover regfile 8 vs 4 - hwsim @ max corner, 2 MHz budget 250 ns ===")
    print(f"Baseline ALU-only SUB B path: {ALU_ONLY_NS} ns (slack {BUDGET_NS - ALU_ONLY_NS} ns)")
    print(f"Target margin: >= {MARGIN_NS} ns E2E (comb + {SETUP_574_NS} ns 574 t_setup)")
    print()
    hdr = (
        f"{'Topology':<42} {'Reg':>3} {'MUX':>4} {'574+':>4} "
        f"{'Comb':>5} {'C_slk':>6} {'E2E':>5} {'E_slk':>6} {'>=15':>5}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['label']:<42} {r['regs']:>3} {r['mux_ic']:>4} {r['574_extra']:>4} "
            f"{r['comb_delay_ns']:>5} {r['comb_slack_ns']:>6} "
            f"{r['e2e_delay_ns']:>5} {r['e2e_slack_ns']:>6} "
            f"{'YES' if r['pass_15ns'] else 'no':>5}"
        )

    best = max(rows, key=lambda r: (r["pass_15ns"], r["e2e_slack_ns"], r["regs"]))
    print()
    print("Recommendation:")
    if best["regs"] == 8 and "151" in best["name"]:
        print(
            f"  -> 8×574 + 8×151/port ({best['mux_ic']} MUX IC). "
            f"E2E slack {best['e2e_slack_ns']} ns @ 2 MHz max corner."
        )
    elif best["regs"] == 4:
        print(
            f"  -> 4×574 + 4×153/port if ISA acceptable; "
            f"E2E slack {best['e2e_slack_ns']} ns."
        )
    else:
        print(f"  -> {best['label']}: E2E slack {best['e2e_slack_ns']} ns.")

    fail = [r for r in rows if not r["pass_15ns"]]
    if fail:
        print("  Avoid for 2 MHz @ max:", ", ".join(r["label"] for r in fail))


if __name__ == "__main__":
    main()
