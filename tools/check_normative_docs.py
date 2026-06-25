#!/usr/bin/env python3
"""Fail if docs/normative/**/*.md contains internal-tool or research backlinks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "docs" / "normative"

FORBIDDEN = [
    (re.compile(r"plover_vm", re.I), "plover_vm"),
    (re.compile(r"\bhwsim\b", re.I), "hwsim"),
    (re.compile(r"\bcyclesim\b", re.I), "cyclesim"),
    (re.compile(r"\bpytest\b", re.I), "pytest"),
    (re.compile(r"cargo\s+run", re.I), "cargo run"),
    (re.compile(r"python\s+-m\s+plover_vm", re.I), "python -m plover_vm"),
    (re.compile(r"python\s+-m\s+hwsim", re.I), "python -m hwsim"),
    (re.compile(r"python\s+-m\s+pytest", re.I), "python -m pytest"),
    (re.compile(r"--engine\s+(micro|macro|fast)", re.I), "--engine micro|macro|fast"),
    (re.compile(r"cpu-4axis", re.I), "cpu-4axis"),
    (re.compile(r"search-report", re.I), "search-report"),
    (re.compile(r"cpld-ctrl-extract", re.I), "cpld-ctrl-extract"),
    (re.compile(r"hardware/research/", re.I), "hardware/research/"),
    (re.compile(r"\.\./hardware/research/", re.I), "../hardware/research/"),
    (re.compile(r"\(research/", re.I), "(research/"),
]


def main() -> int:
    if not NORMATIVE.is_dir():
        print(f"missing {NORMATIVE}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in sorted(NORMATIVE.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, label in FORBIDDEN:
                if pattern.search(line):
                    errors.append(f"{rel}:{line_no}: forbidden {label}: {line.strip()[:120]}")
                    break

    if errors:
        print("normative doc governance violations:\n", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        print(f"\n{len(errors)} violation(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(list(NORMATIVE.rglob('*.md')))} normative markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
