#!/usr/bin/env python3
"""Create a blank PLFS image and optionally inject a file (S7b)."""

from __future__ import annotations

import argparse
from pathlib import Path

from kern.plfs import Plfs
from kern.vfdd import VfddDriver
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sectors", type=int, default=64)
    ap.add_argument("--inject", type=Path)
    ap.add_argument("--name", type=str, default="HELLO.PLR")
    args = ap.parse_args()

    dev = VirtualFdd(VfdConfig(path=args.out, sector_count=args.sectors))
    fs = Plfs(VfddDriver(dev))
    fs.format()
    if args.inject:
        fs.create(args.name, args.inject.read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

