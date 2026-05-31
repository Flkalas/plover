#!/usr/bin/env python3
"""Pack 16-bit control words into rom_low.hex / rom_high.hex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def pack(words: list[int], out_dir: Path) -> None:
    lo = [w & 0xFF for w in words]
    hi = [(w >> 8) & 0xFF for w in words]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rom_low.hex").write_text(
        "\n".join(f"{b:02x}" for b in lo) + "\n", encoding="utf-8"
    )
    (out_dir / "rom_high.hex").write_text(
        "\n".join(f"{b:02x}" for b in hi) + "\n", encoding="utf-8"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "words",
        nargs="*",
        help="16-bit hex values e.g. 9510 0005",
    )
    ap.add_argument("-f", "--file", type=Path, help="one hex word per line")
    ap.add_argument("-o", "--out-dir", type=Path, default=Path("sim"))
    args = ap.parse_args()

    values: list[int] = []
    if args.file:
        for line in args.file.read_text(encoding="utf-8").splitlines():
            line = line.split(";", 1)[0].strip()
            if not line:
                continue
            values.append(int(line, 16))
    else:
        for w in args.words:
            values.append(int(w, 16))

    if not values:
        print("no words", file=sys.stderr)
        return 1

    pack(values, args.out_dir)
    print(f"packed {len(values)} words -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
