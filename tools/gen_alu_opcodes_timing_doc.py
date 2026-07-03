#!/usr/bin/env python3
"""Regenerate §3.1 timing table in docs/normative/hardware/alu-opcodes-timing.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES  # noqa: E402

DOC = ROOT / "docs" / "normative" / "hardware" / "alu-opcodes-timing.md"
REPORT = ROOT / "build" / "hwsim" / "alu8_opcode_timing" / "timing_report.json"
START = "<!-- TIMING_TABLE_START -->"
END = "<!-- TIMING_TABLE_END -->"
BUDGET = 250

_NOTES = {
    "NOP": "sum path (Y=0)",
    "ADD": "283 → **157_YBP**",
    "SUB": "153 mux2 → 283",
    "AND": "`U_ALU_153_0` mux1 → 157_YBP",
    "OR": "",
    "XOR": "",
    "NOT": "",
    "PASS_A": "AND pattern + B=FF",
    "PASS_B": "AND pattern + A=FF",
    "INC": "`net_cin` → 283 ripple",
    "DEC": "283-only test path; full path = SUB class",
    "CMP": "Y = SUB; flags §3.5",
}

_GRADE = {
    "NOP": "adder",
    "ADD": "adder",
    "SUB": "arith B-path",
    "AND": "logic",
    "OR": "logic",
    "XOR": "logic",
    "NOT": "logic",
    "PASS_A": "logic",
    "PASS_B": "logic",
    "INC": "**critical**",
    "DEC": "adder",
    "CMP": "arith B-path",
}


def _load_delays() -> list[int]:
    if not REPORT.is_file():
        raise SystemExit(f"missing {REPORT} — run hwsim alu8_opcode_timing first")
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    checks = [c for c in data.get("checks", []) if c.get("type") == "slack"]
    if len(checks) != len(CASES):
        raise SystemExit(f"expected {len(CASES)} slack checks, got {len(checks)}")
    return [int(c["delay_ns"]) for c in checks]


def _render_table(delays: list[int]) -> str:
    lines = [
        "| sel | Op | 경로 등급 | max (ns) | slack @ max (ns) | 비고 |",
        "|-----|-----|-----------|----------|------------------|------|",
    ]
    for i, ((name, *_rest), delay) in enumerate(zip(CASES, delays)):
        slack = BUDGET - delay
        note = _NOTES.get(name, "")
        lines.append(
            f"| {i} | {name} | {_GRADE[name]} | **{delay}** | {slack} | {note} |"
        )
    return "\n".join(lines)


def main() -> None:
    delays = _load_delays()
    table = _render_table(delays)
    text = DOC.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit(f"markers not found in {DOC}")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    new_text = f"{before}{START}\n{table}\n{END}{after}"
    DOC.write_text(new_text, encoding="utf-8")
    print(f"updated {DOC} ({len(CASES)} rows from {REPORT.name})")


if __name__ == "__main__":
    main()
