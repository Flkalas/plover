"""CLI: python -m plover_asm build ..."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from plover_asm.assemble import assemble_file
from plover_asm.emit import write_hex, write_listing, write_map
from plover_ld.format import PlxObject, Symbol, write_plx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plover_asm")
    sub = ap.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build", help="Assemble .asm to .sram.hex")
    build.add_argument("inputs", nargs="+", type=Path)
    build.add_argument("-o", "--out", type=Path, required=True)
    build.add_argument("--origin", type=lambda x: int(x, 0), default=0)
    build.set_defaults(func=_cmd_build)

    obj = sub.add_parser("obj", help="Assemble .asm to .plx object")
    obj.add_argument("inputs", nargs="+", type=Path)
    obj.add_argument("-o", "--out", type=Path, required=True)
    obj.add_argument("--origin", type=lambda x: int(x, 0), default=0)
    obj.set_defaults(func=_cmd_obj)

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


def _cmd_obj(args: argparse.Namespace) -> int:
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    for inp in args.inputs:
        result = assemble_file(str(inp), origin=args.origin)
        syms = []
        for name, addr in sorted(result.symbols.items()):
            syms.append(Symbol(name=name, section="text", offset=(addr - result.origin) & 0xFFFF, binding="global", type="func"))
        entry = "main" if any(s.name == "main" for s in syms) else (syms[0].name if syms else None)
        obj = PlxObject(
            name=inp.stem,
            text=list(result.bytes),
            data=[],
            symbols=syms,
            relocs=[],
            entry_symbol=entry,
        )
        out_path = out_dir / f"{inp.stem}.plx"
        write_plx(obj, out_path)
        print(f"{inp.name}: {len(result.bytes)} bytes -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
