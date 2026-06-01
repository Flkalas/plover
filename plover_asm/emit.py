"""Emit hex, listing, map files."""

from __future__ import annotations

from pathlib import Path

from plover_asm.assemble import AsmResult


def write_hex(result: AsmResult, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(f"{b:02X}" for b in result.bytes) + "\n", encoding="utf-8")


def write_listing(result: AsmResult, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(result.listing) + "\n", encoding="utf-8")


def write_map(result: AsmResult, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{name} = ${addr:04X}" for name, addr in sorted(result.symbols.items())]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
