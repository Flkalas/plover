#!/usr/bin/env python3
"""Emit system_ctrl.pin from WinCUPL fitter PLCC44 Pin/Node Placement."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIT = ROOT / "system_ctrl_gen.fit"
OUT = ROOT / "system_ctrl.pin"

PIN_LINE = re.compile(r"^Pin\s+(\d+)\s+=\s+(\w+);", re.MULTILINE)

JTAG = {7: "TDI", 13: "TMS", 32: "TCK", 38: "TDO"}


def main() -> int:
    if not FIT.is_file():
        print(f"missing {FIT} — run build-wincupl.ps1 first", file=sys.stderr)
        return 1

    text = FIT.read_text(encoding="utf-8", errors="replace")
    block = text.split("PLCC44 Pin/Node Placement:", 1)
    if len(block) < 2:
        print("Pin/Node Placement section not found in .fit", file=sys.stderr)
        return 1

    assignments: dict[int, str] = {}
    for pin_s, sig in PIN_LINE.findall(block[1]):
        pin = int(pin_s)
        if pin in JTAG:
            continue
        assignments[pin] = sig

    lines = [
        "# WinCUPL pin lock — ATF1504AS-10JU44 (from system_ctrl_gen.fit)",
        "# Source PLD: cpld_fsm/hdl/system_ctrl.pld",
        "# Regenerate: python gen_pin_lock.py (after build-wincupl.ps1)",
        "",
        "DEVICE f1504ispplcc44",
        "",
        "# JTAG ISP (reserved during program)",
        "# TDI=7 TMS=13 TCK=32 TDO=38",
        "",
    ]

    for pin in sorted(assignments):
        lines.append(f"PIN {pin:2d} = {assignments[pin]}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(assignments)} user I/O pins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
