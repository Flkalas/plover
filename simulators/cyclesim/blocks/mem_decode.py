"""Memory map decode — MAP_MODE, mailbox, boot ROM (functional 138 glue equivalent)."""

from __future__ import annotations

BOOT_ROM_END = 0x07FF
MAILBOX_BASE = 0xFF00
MAILBOX_END = 0xFFFB
VECTOR_ADDR = 0xFFFC


def mailbox_en(addr: int) -> bool:
    a = addr & 0xFFFF
    return MAILBOX_BASE <= a <= MAILBOX_END


class MemSystem:
    """Behavioral memory map per memory-map.md v1.0."""

    def __init__(self) -> None:
        self.map_mode = 0
        self.rom: dict[int, int] = {}
        self.ram: dict[int, int] = {}
        self.mailbox: dict[int, int] = {}

    def reset_vector(self) -> int:
        lo = self.read(VECTOR_ADDR)
        hi = self.read(VECTOR_ADDR + 1)
        return lo | (hi << 8)

    def read(self, addr: int) -> int:
        addr &= 0xFFFF
        if mailbox_en(addr):
            return self.mailbox.get(addr - MAILBOX_BASE, 0) & 0xFF
        if self.map_mode == 0 and addr <= BOOT_ROM_END:
            return self.rom.get(addr, 0) & 0xFF
        if self.map_mode == 0 and addr >= VECTOR_ADDR:
            return self.rom.get(addr, 0) & 0xFF
        return self.ram.get(addr, 0) & 0xFF

    def write(self, addr: int, val: int) -> None:
        addr &= 0xFFFF
        val &= 0xFF
        if mailbox_en(addr):
            self.mailbox[addr - MAILBOX_BASE] = val
            return
        if self.map_mode == 0 and addr <= BOOT_ROM_END:
            return
        if self.map_mode == 0 and addr >= VECTOR_ADDR:
            return
        self.ram[addr] = val

    def load_hex(self, path: str, *, target: str = "rom") -> None:
        store = self.rom if target == "rom" else self.ram
        addr = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for tok in line.split():
                    store[addr] = int(tok, 16) & 0xFF
                    addr += 1

    def load_bytes(self, base: int, blob: bytes, *, target: str = "rom") -> None:
        store = self.rom if target == "rom" else self.ram
        for i, b in enumerate(blob):
            store[base + i] = b

    def load_ram(self, addr: int, val: int) -> None:
        self.ram[addr & 0xFFFF] = val & 0xFF

    def set_vector(self, pc: int) -> None:
        pc &= 0xFFFF
        self.rom[VECTOR_ADDR] = pc & 0xFF
        self.rom[VECTOR_ADDR + 1] = (pc >> 8) & 0xFF
