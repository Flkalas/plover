#!/usr/bin/env python3
"""Compile Tiny BASIC+Game subset to token bytecode for Plover VM (TOK_BASE=$2800)."""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

TOK_END = 0xFF
TOK_CLS = 0x87
TOK_PRINT_STR = 0x83
TOK_LET_IMM = 0x84
TOK_GOTO = 0x85
TOK_INKEY_VAR = 0x88
TOK_IF_KEY_NEQ = 0x89
TOK_ADD_VAR_IMM = 0x8A
TOK_SPRITE_VAR = 0xA1
TOK_DRAW = 0xA2
TOK_SOUND = 0xA3
TOK_LAYER_SCROLL = 0xA4
TOK_TILE = 0xA5

TOK_BASE = 0x2800


def var_idx(name: str) -> int:
    name = name.strip().upper()
    if len(name) != 1 or not ("A" <= name <= "Z"):
        raise ValueError(f"variable must be A-Z: {name!r}")
    return ord(name) - ord("A")


def parse_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^(\d+)\s+(.*)$", line, re.I)
        if not m:
            raise ValueError(f"missing line number: {line!r}")
        out.append((int(m.group(1)), m.group(2).strip()))
    out.sort(key=lambda x: x[0])
    return out


def compile_stmt(stmt: str, out: list[bytes], line_addrs: dict[int, int]) -> None:
    u = stmt.upper()

    if u == "CLS":
        out.append(bytes([TOK_CLS]))
        return

    if u == "DRAW":
        out.append(bytes([TOK_DRAW]))
        return

    m = re.match(r'^PRINT\s+"([^"]*)"\s*$', stmt, re.I)
    if m:
        s = m.group(1).encode("ascii", errors="replace")
        out.append(bytes([TOK_PRINT_STR, len(s)]) + s)
        return

    m = re.match(r"^LET\s+([A-Z])\s*=\s*(\d+)\s*$", stmt, re.I)
    if m:
        out.append(bytes([TOK_LET_IMM, var_idx(m.group(1)), int(m.group(2)) & 0xFF]))
        return

    m = re.match(r"^GOTO\s+(\d+)\s*$", stmt, re.I)
    if m:
        ln = int(m.group(1))
        out.append(bytes([TOK_GOTO]) + struct.pack("<H", line_addrs[ln]))
        return

    m = re.match(r"^([A-Z])\s*=\s*INKEY\s*\(\s*\)\s*$", stmt, re.I)
    if m:
        out.append(bytes([TOK_INKEY_VAR, var_idx(m.group(1))]))
        return

    m = re.match(r"^IF\s+INKEY\s*\(\s*\)\s*<>\s*(\d+)\s+THEN\s+GOTO\s+(\d+)\s*$", stmt, re.I)
    if m:
        key = int(m.group(1)) & 0xFF
        target = line_addrs[int(m.group(2))]
        out.append(bytes([TOK_IF_KEY_NEQ, key]) + struct.pack("<H", target))
        return

    m = re.match(r"^LET\s+([A-Z])\s*=\s*([A-Z])\s*\+\s*(\d+)\s*$", stmt, re.I)
    if m:
        dst, src, delta = m.group(1), m.group(2), int(m.group(3))
        if dst.upper() != src.upper():
            raise ValueError("only LET X = X + n supported")
        out.append(bytes([TOK_ADD_VAR_IMM, var_idx(dst), delta & 0xFF]))
        return

    m = re.match(r"^SPRITE\s+(\d+)\s*,\s*([A-Z])\s*,\s*([A-Z])\s*,\s*(\d+)\s*,\s*(\d+)\s*$", stmt, re.I)
    if m:
        out.append(
            bytes(
                [
                    TOK_SPRITE_VAR,
                    int(m.group(1)) & 0xFF,
                    var_idx(m.group(2)),
                    var_idx(m.group(3)),
                    int(m.group(4)) & 0xFF,
                    int(m.group(5)) & 0xFF,
                ]
            )
        )
        return

    m = re.match(r"^SOUND\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$", stmt, re.I)
    if m:
        ch, hz, dur = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out.append(bytes([TOK_SOUND, ch & 0xFF]) + struct.pack("<H", hz) + bytes([dur & 0xFF]))
        return

    m = re.match(r"^LAYER\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$", stmt, re.I)
    if m:
        out.append(
            bytes(
                [
                    TOK_LAYER_SCROLL,
                    int(m.group(1)) & 0xFF,
                    int(m.group(2)) & 0xFF,
                    int(m.group(3)) & 0xFF,
                ]
            )
        )
        return

    m = re.match(r"^TILE\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$", stmt, re.I)
    if m:
        out.append(
            bytes(
                [
                    TOK_TILE,
                    int(m.group(1)) & 0xFF,
                    int(m.group(2)) & 0xFF,
                    int(m.group(3)) & 0xFF,
                    int(m.group(4)) & 0xFF,
                ]
            )
        )
        return

    raise ValueError(f"unsupported statement: {stmt!r}")


def compile_basic(text: str, base: int = TOK_BASE) -> bytes:
    lines = parse_lines(text)
    line_code: list[tuple[int, bytes]] = []
    for ln, stmt in lines:
        buf: list[bytes] = []
        compile_stmt(stmt, buf, {l: 0 for l, _ in lines})
        line_code.append((ln, b"".join(buf)))

    addrs: dict[int, int] = {}
    cursor = base
    for ln, code in line_code:
        addrs[ln] = cursor
        cursor += len(code)

    line_code2: list[bytes] = []
    for ln, stmt in lines:
        buf: list[bytes] = []
        compile_stmt(stmt, buf, addrs)
        line_code2.append(b"".join(buf))

    return b"".join(line_code2) + bytes([TOK_END])


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) < 1:
        print("usage: tokenize.py input.bas [output.tok]", file=sys.stderr)
        return 2
    src = Path(argv[0])
    text = src.read_text(encoding="utf-8")
    blob = compile_basic(text)
    if len(argv) >= 2:
        Path(argv[1]).write_bytes(blob)
    else:
        sys.stdout.buffer.write(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
