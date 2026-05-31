"""64 KiB logical RAM (2×32K A15 bank unified)."""

from __future__ import annotations

RAM_SIZE = 64 * 1024


class Ram64K:
    def __init__(self) -> None:
        self._mem = bytearray(RAM_SIZE)

    def read(self, addr: int) -> int:
        return self._mem[addr & 0xFFFF]

    def write(self, addr: int, val: int) -> None:
        self._mem[addr & 0xFFFF] = val & 0xFF

    def load(self, data: bytes | bytearray, base: int = 0) -> None:
        for i, b in enumerate(data):
            self.write(base + i, b)

    def snapshot(self) -> bytes:
        return bytes(self._mem)
