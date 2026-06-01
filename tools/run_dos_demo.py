#!/usr/bin/env python3
"""Run a scripted PL-DOS demo (S7d)."""

from __future__ import annotations

from pathlib import Path

from plover_vm.dos_scenario import run_dos_scenario


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    doc = {"kind": "dos", "actions": [{"type": "dir"}, {"type": "run", "name": "HELLO.PLR"}]}
    res = run_dos_scenario(doc, root=root)
    for line in res.output:
        print(line)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

