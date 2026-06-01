"""CLI: compile subset-C to .sram.hex via plover_asm."""

from __future__ import annotations

import argparse
from pathlib import Path

from plover_asm.assemble import assemble
from plover_asm.emit import write_hex
from plover_cc.codegen import program_to_asm
from plover_cc.parse import parse
from plover_ld.format import PlxObject, Symbol, write_plx


def main() -> int:
    ap = argparse.ArgumentParser(prog="plover_cc")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("-c", "--object", action="store_true", help="emit .plx object instead of .sram.hex")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8")
    prog = parse(text)
    asm = program_to_asm(prog)
    res = assemble(asm, origin=0)
    if args.object:
        obj = PlxObject(
            name=args.input.stem,
            text=list(res.bytes),
            data=[],
            symbols=[
                Symbol(name="main", section="text", offset=0, binding="global", type="func"),
            ],
            relocs=[],
            entry_symbol="main",
        )
        write_plx(obj, args.out)
    else:
        write_hex(res, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

