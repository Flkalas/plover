"""PLFS v0.1 flat catalog filesystem (S7b)."""

from __future__ import annotations

from dataclasses import dataclass

from kern.vfdd import VfddDriver
from plover_vm.memory.vfdd import SECTOR_SIZE


DIR_SECTOR = 1
DATA_BASE = 2

ENTRY_SIZE = 16
ENTRIES_PER_SECTOR = SECTOR_SIZE // ENTRY_SIZE


def _norm_name(name: str) -> bytes:
    # 8.3 upper, padded with spaces to 11 bytes.
    base = name.upper()
    if "." in base:
        a, b = base.split(".", 1)
    else:
        a, b = base, ""
    a = (a[:8]).ljust(8)
    b = (b[:3]).ljust(3)
    return (a + b).encode("ascii", errors="replace")


@dataclass(frozen=True)
class DirEntry:
    name11: bytes
    start_sector: int
    size_bytes: int
    attr: int = 0

    def pack(self) -> bytes:
        return (
            self.name11[:11]
            + bytes([self.start_sector & 0xFF, (self.start_sector >> 8) & 0xFF])
            + bytes([self.size_bytes & 0xFF, (self.size_bytes >> 8) & 0xFF])
            + bytes([self.attr & 0xFF])
        ).ljust(ENTRY_SIZE, b"\x00")

    @classmethod
    def unpack(cls, data: bytes) -> "DirEntry | None":
        if len(data) != ENTRY_SIZE:
            raise ValueError("bad entry size")
        name = data[:11]
        if name == b"\x00" * 11 or name == b" " * 11:
            return None
        start = data[11] | (data[12] << 8)
        size = data[13] | (data[14] << 8)
        attr = data[15]
        return cls(name11=name, start_sector=start, size_bytes=size, attr=attr)


class Plfs:
    def __init__(self, drv: VfddDriver) -> None:
        self.drv = drv

    def format(self) -> None:
        # sector0 reserved for future BPB; zero directory sector.
        self.drv.write_sector(DIR_SECTOR, b"\x00" * SECTOR_SIZE)

    def _load_dir(self) -> list[DirEntry | None]:
        sec = self.drv.read_sector(DIR_SECTOR)
        out: list[DirEntry | None] = []
        for i in range(ENTRIES_PER_SECTOR):
            chunk = sec[i * ENTRY_SIZE : (i + 1) * ENTRY_SIZE]
            out.append(DirEntry.unpack(chunk))
        return out

    def _store_dir(self, entries: list[DirEntry | None]) -> None:
        buf = bytearray(SECTOR_SIZE)
        for i, e in enumerate(entries[:ENTRIES_PER_SECTOR]):
            if e is None:
                continue
            buf[i * ENTRY_SIZE : (i + 1) * ENTRY_SIZE] = e.pack()
        self.drv.write_sector(DIR_SECTOR, bytes(buf))

    def list(self) -> list[DirEntry]:
        return [e for e in self._load_dir() if e is not None]

    def _find(self, name: str) -> tuple[int, DirEntry] | None:
        want = _norm_name(name)
        for i, e in enumerate(self._load_dir()):
            if e is None:
                continue
            if e.name11 == want:
                return i, e
        return None

    def create(self, name: str, data: bytes) -> None:
        if self._find(name) is not None:
            raise FileExistsError(name)
        entries = self._load_dir()
        try:
            slot = entries.index(None)
        except ValueError:
            raise RuntimeError("directory full")

        # Find first free data sector after existing files (contiguous policy).
        used_end = DATA_BASE
        for e in entries:
            if e is None:
                continue
            end = e.start_sector + ((e.size_bytes + SECTOR_SIZE - 1) // SECTOR_SIZE)
            used_end = max(used_end, end)
        start = used_end
        nsectors = (len(data) + SECTOR_SIZE - 1) // SECTOR_SIZE
        for s in range(nsectors):
            chunk = data[s * SECTOR_SIZE : (s + 1) * SECTOR_SIZE].ljust(SECTOR_SIZE, b"\x00")
            self.drv.write_sector(start + s, chunk)

        entries[slot] = DirEntry(name11=_norm_name(name), start_sector=start, size_bytes=len(data))
        self._store_dir(entries)

    def read(self, name: str) -> bytes:
        found = self._find(name)
        if found is None:
            raise FileNotFoundError(name)
        _, e = found
        nsectors = (e.size_bytes + SECTOR_SIZE - 1) // SECTOR_SIZE
        buf = bytearray()
        for s in range(nsectors):
            buf.extend(self.drv.read_sector(e.start_sector + s))
        return bytes(buf[: e.size_bytes])

    def delete(self, name: str) -> None:
        found = self._find(name)
        if found is None:
            raise FileNotFoundError(name)
        idx, _e = found
        entries = self._load_dir()
        entries[idx] = None
        self._store_dir(entries)

