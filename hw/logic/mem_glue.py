"""Discrete gate helpers for breadboard mailbox / MAP qualifiers (v1.0)."""

from __future__ import annotations


def mailbox_en(addr: int) -> int:
    """$FF00–$FFFB — matches decode_addr / memory-map.md."""
    a = addr & 0xFFFF
    return 1 if 0xFF00 <= a <= 0xFFFB else 0


def boot_rom_window(addr: int, map_mode: int) -> int:
    """Mode A: $0000–$07FF ROM (A11=0 in low half)."""
    if map_mode != 0:
        return 0
    return 1 if (addr & 0xFFFF) < 0x0800 else 0


def vector_rom_window(addr: int, map_mode: int) -> int:
    """$FFFC–$FFFF ROM in Mode A; RAM in Mode B."""
    if map_mode != 0:
        return 0
    return 1 if (addr & 0xFFFF) >= 0xFFFC else 0
