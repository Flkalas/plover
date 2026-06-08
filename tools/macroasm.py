#!/usr/bin/env python3
"""Minimal v1.0 macro assembler -> SRAM byte image."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OPCODES = {
    "ADD": 0x01,
    "LDA": 0x02,
    "STA": 0x03,
    "BEQ": 0x04,
    "JMP": 0x05,
    "CALL": 0x06,
    "RET": 0x07,
    "LDIO": 0x08,
    "STIO": 0x09,
    "HALT": 0x0A,
    "ADD_RR": 0x0B,
    "MOV": 0x0C,
    "CMP": 0x0D,
    "BCS": 0x0E,
    "WADD_RR": 0x10,
    "WMOV": 0x11,
    "WCMP16": 0x12,
}

WIDE_IMM16 = frozenset({"WCMP16"})


def encode_line(line: str) -> list[int] | None:
    line = line.split(";", 1)[0].strip()
    if not line or line.startswith("#"):
        return None
    m = re.match(r"(\w+)\s*(.*)", line)
    if not m:
        raise ValueError(f"bad line: {line}")
    mnem, rest = m.group(1).upper(), m.group(2).strip()
    if mnem not in OPCODES:
        raise ValueError(f"unknown mnemonic: {mnem}")
    op = OPCODES[mnem]
    imm = 0
    if rest:
        imm = int(rest, 0)
    if mnem in WIDE_IMM16:
        imm &= 0xFFFF
        return [op, imm & 0xFF, (imm >> 8) & 0xFF]
    return [op, imm & 0xFF]


def assemble(text: str) -> list[int]:
    mem: list[int] = []
    for line in text.splitlines():
        enc = encode_line(line)
        if enc is None:
            continue
        mem.extend(enc)
    return mem


def write_hex(bytes_: list[int], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{b:02X}" for b in bytes_]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, nargs="?", help=".pls source")
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--build-fixtures", action="store_true")
    args = ap.parse_args()

    if args.build_fixtures:
        fixtures = ROOT / "hw" / "fixtures" / "sram"
        fixtures.mkdir(parents=True, exist_ok=True)
        prog = "\n".join(
            [
                "; normative ADD: R2 <- R0+R1, imm -> R1 (init R0=0x12 in scenario)",
                "ADD 0x34",
                "HALT",
            ]
        )
        write_hex(assemble(prog), fixtures / "add_imm.sram.hex")
        fib = "\n".join(
            [
                "; fib counter",
                "ADD 1",
                "BEQ 0",
            ]
        )
        write_hex(assemble(fib), fixtures / "fib_loop.sram.hex")
        print(f"wrote fixtures under {fixtures}")
        return

    src = args.input.read_text(encoding="utf-8") if args.input else ""
    mem = assemble(src)
    out = args.out or Path("program.sram.hex")
    write_hex(mem, out)
    print(f"wrote {len(mem)} bytes -> {out}")


if __name__ == "__main__":
    main()
