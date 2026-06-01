"""CLI for plover_ld."""

from __future__ import annotations

import argparse
from pathlib import Path

from plover_ld.linker import link_paths_to_plr


def main() -> int:
    ap = argparse.ArgumentParser(prog="plover_ld")
    ap.add_argument("objects", nargs="+", type=Path, help=".plx object files")
    ap.add_argument("-o", "--out", required=True, type=Path, help="output .plr")
    ap.add_argument("--map", dest="map_path", type=Path, help="optional symbol map output")
    ap.add_argument("--text-base", type=lambda s: int(s, 0), default=0x2800)
    ap.add_argument("--entry", dest="entry_symbol", default=None)
    args = ap.parse_args()

    lr = link_paths_to_plr(
        args.objects,
        args.out,
        text_base=args.text_base,
        entry_symbol=args.entry_symbol,
        map_path=args.map_path,
    )
    print(f"linked {len(args.objects)} objects, relocs={lr.reloc_applied}, symbols={len(lr.symbols)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

