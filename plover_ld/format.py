"""PLX object format helpers (JSON container for MVP)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MAGIC = "PLX\0"
VERSION = 1


@dataclass(frozen=True)
class Symbol:
    name: str
    section: str  # text|data|abs|undef
    offset: int
    binding: str = "global"
    type: str = "func"


@dataclass(frozen=True)
class Reloc:
    section: str  # text|data
    offset: int
    kind: str  # abs16|rel8
    symbol: str


@dataclass
class PlxObject:
    name: str
    text: list[int] = field(default_factory=list)
    data: list[int] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    relocs: list[Reloc] = field(default_factory=list)
    entry_symbol: str | None = "main"

    def to_dict(self) -> dict:
        return {
            "magic": MAGIC,
            "version": VERSION,
            "name": self.name,
            "entry_symbol": self.entry_symbol,
            "text": [b & 0xFF for b in self.text],
            "data": [b & 0xFF for b in self.data],
            "symbols": [s.__dict__ for s in self.symbols],
            "relocs": [r.__dict__ for r in self.relocs],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PlxObject":
        if d.get("magic") != MAGIC:
            raise ValueError("bad PLX magic")
        symbols = [Symbol(**s) for s in d.get("symbols", [])]
        relocs = [Reloc(**r) for r in d.get("relocs", [])]
        return cls(
            name=d.get("name", "obj"),
            text=list(d.get("text", [])),
            data=list(d.get("data", [])),
            symbols=symbols,
            relocs=relocs,
            entry_symbol=d.get("entry_symbol", "main"),
        )


def write_plx(obj: PlxObject, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj.to_dict(), indent=2) + "\n", encoding="utf-8")


def read_plx(path: Path | str) -> PlxObject:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    return PlxObject.from_dict(d)

