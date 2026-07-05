#!/usr/bin/env python3
"""Write ATF1504AS erased-fuse JEDEC stub until ProChip fit replaces it."""

from __future__ import annotations

from pathlib import Path

# ATF1504AS JED fuse count (prjbureau fuseconv ATF1504AS map)
FUSE_COUNT = 34192
OUT = Path(__file__).resolve().parent / "system_ctrl.jed"


def main() -> None:
    lines = [
        "NOTE Plover system_ctrl - ERASED-FUSE STUB",
        "NOTE Replace with ProChip Designer fit output before silicon bring-up",
        "NOTE Device ATF1504AS-10JU44 PLCC-44",
        "QEPLD*",
        f"QF{FUSE_COUNT}*",
        "G0*",
        "F0*",
    ]
    # Erased CPLD: all fuses = 1 (JED '1' = blown/programmed in some devices; blank-check uses device-specific polarity)
    chunk = 80
    ones = "1" * chunk
    for start in range(0, FUSE_COUNT, chunk):
        n = min(chunk, FUSE_COUNT - start)
        lines.append(f"L{start:05d} " + "1" * n)
    lines.append("*")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="ascii")
    print(f"Wrote {OUT} ({FUSE_COUNT} fuses, stub - run ProChip fit to replace)")


if __name__ == "__main__":
    main()
