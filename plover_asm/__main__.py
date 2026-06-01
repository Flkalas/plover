"""CLI: python -m plover_asm build ..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_asm.emit import write_hex, write_listing, write_map


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plover_asm")
    sub = ap.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build", help="Assemble .asm to .sram.hex")
    build.add_argument("inputs", nargs="+", type=Path)
    build.add_argument("-o", "--out", type=Path, required=True)
    build.add_argument("--origin", type=lambda x: int(x, 0), default=0)
    build.set_defaults(func=_cmd_build)

    args = ap.parse_args(argv)
    return args.func(args)


def _cmd_build(args: argparse.Namespace) -> int:
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    for inp in args.inputs:
        result = assemble_file(str(inp), origin=args.origin)
        stem = inp.stem
        write_hex(result, out_dir / f"{stem}.sram.hex")
        write_listing(result, out_dir / f"{stem}.lst")
        write_map(result, out_dir / f"{stem}.map")
        print(f"{inp.name}: {len(result.bytes)} bytes -> {out_dir / stem}.sram.hex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
