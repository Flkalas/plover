"""SST39SF010A 128K×8 NOR flash."""

from __future__ import annotations

from pathlib import Path

from plover_vm.loader import load_hex, load_hex_sparse

NOR_SIZE = 128 * 1024
CW_FLASH_BASE = 0x4000


class NorFlash:
    def __init__(self) -> None:
        self._mem = bytearray(NOR_SIZE)

    def load_hex(self, path: Path | str, offset: int = 0) -> None:
        chunk, _end = load_hex(path, offset)
        for i, b in enumerate(chunk):
            if offset + i < NOR_SIZE:
                self._mem[offset + i] = b

    def load_image(self, path: Path | str) -> None:
        self._mem = load_hex_sparse(path, NOR_SIZE, 0)

    def read(self, flash_offset: int) -> int:
        return self._mem[flash_offset & (NOR_SIZE - 1)]

    def cpu_map_read(self, cpu_addr: int) -> int:
        """CPU-visible ROM windows in Mode A."""
        a = cpu_addr & 0xFFFF
        if a < 0x0800:
            return self.read(a)
        if a >= 0xFFFC:
            return self.read(a)
        return 0xFF

    def read_cw(self, store_index: int) -> int:
        """10-bit CW: lo @ 2*idx, hi (REG_SEL) @ 2*idx+1."""
        idx = (store_index & 0x7FF) * 2
        lo = self.read(CW_FLASH_BASE + idx)
        hi = self.read(CW_FLASH_BASE + idx + 1)
        return lo | (hi << 8)

    def patch_cw_region(self, words: list[int], base: int = CW_FLASH_BASE) -> None:
        for i, w in enumerate(words):
            off = base + i
            if off < NOR_SIZE:
                self._mem[off] = w & 0xFF
