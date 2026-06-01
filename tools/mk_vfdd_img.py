#!/usr/bin/env python3
"""Create a bootable PL-DOS PLFS image."""

from __future__ import annotations

import argparse
from pathlib import Path

from kern.plfs import Plfs
from kern.plr import PlrImage, pack_plr
from kern.vfdd import VfddDriver
from plover_asm.assemble import assemble
from plover_vm.memory.vfdd import VfdConfig, VirtualFdd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sectors", type=int, default=64)
    ap.add_argument("--bootable", action="store_true", help="populate stage0/stage1/shell defaults")
    ap.add_argument("--inject", type=Path)
    ap.add_argument("--name", type=str, default="HELLO.PLR")
    args = ap.parse_args()

    dev = VirtualFdd(VfdConfig(path=args.out, sector_count=args.sectors))
    fs = Plfs(VfddDriver(dev))
    fs.format()
    if args.bootable:
        # sector0 stage1 bootstrap placeholder
        fs.drv.write_sector(0, b"PLDOS_STAGE1".ljust(512, b"\x00"))
        # default shell/app payloads
        hello_res = assemble("        .ORG 0\n        ADD 7\n        HALT\n", origin=0)
        hello = pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(hello_res.bytes)))
        fs.create("HELLO.PLR", hello)
        command = pack_plr(PlrImage(load_addr=0x3000, entry_off=0, code=b"\x0A"))
        fs.create("COMMAND.PLR", command)
        fs.create("README.TXT", b"PL-DOS boot image")
    if args.inject:
        fs.create(args.name, args.inject.read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

