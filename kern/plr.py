"""Plover executable format (.PLR) helpers (S7c)."""

from __future__ import annotations

from dataclasses import dataclass


MAGIC = b"PLR\x00"
HEADER_SIZE = 10


@dataclass(frozen=True)
class PlrImage:
    load_addr: int
    entry_off: int
    code: bytes

    @property
    def entry_addr(self) -> int:
        return (self.load_addr + self.entry_off) & 0xFFFF


def pack_plr(img: PlrImage) -> bytes:
    code = bytes(img.code)
    size = len(code) & 0xFFFF
    hdr = bytearray()
    hdr += MAGIC
    hdr += bytes([img.load_addr & 0xFF, (img.load_addr >> 8) & 0xFF])
    hdr += bytes([size & 0xFF, (size >> 8) & 0xFF])
    hdr += bytes([img.entry_off & 0xFF, (img.entry_off >> 8) & 0xFF])
    return bytes(hdr) + code


def unpack_plr(data: bytes) -> PlrImage:
    if len(data) < HEADER_SIZE:
        raise ValueError("short .PLR")
    if data[:4] != MAGIC:
        raise ValueError("bad magic")
    load = data[4] | (data[5] << 8)
    size = data[6] | (data[7] << 8)
    entry = data[8] | (data[9] << 8)
    code = data[10 : 10 + size]
    if len(code) != size:
        raise ValueError("truncated payload")
    return PlrImage(load_addr=load, entry_off=entry, code=bytes(code))

