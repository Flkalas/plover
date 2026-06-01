"""Virtual floppy disk device: 512-byte sectors in a host .img file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SECTOR_SIZE = 512


@dataclass(frozen=True)
class VfdConfig:
    path: Path
    sector_count: int


class VirtualFdd:
    def __init__(self, cfg: VfdConfig) -> None:
        self.cfg = cfg
        self.cfg.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.cfg.path.exists():
            self.cfg.path.write_bytes(b"\x00" * (self.cfg.sector_count * SECTOR_SIZE))

    def read_sector(self, n: int) -> bytes:
        if n < 0 or n >= self.cfg.sector_count:
            raise IndexError("sector out of range")
        with self.cfg.path.open("rb") as f:
            f.seek(n * SECTOR_SIZE)
            data = f.read(SECTOR_SIZE)
        if len(data) != SECTOR_SIZE:
            raise IOError("short read")
        return data

    def write_sector(self, n: int, data: bytes) -> None:
        if n < 0 or n >= self.cfg.sector_count:
            raise IndexError("sector out of range")
        if len(data) != SECTOR_SIZE:
            raise ValueError("sector must be 512 bytes")
        with self.cfg.path.open("r+b") as f:
            f.seek(n * SECTOR_SIZE)
            f.write(data)

