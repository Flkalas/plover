"""MMIO effective address helper for LDIO/STIO (offset in operand byte)."""

from __future__ import annotations

MB_BASE = 0xFF00


def mmio_addr(offset: int) -> int:
    return (MB_BASE | (offset & 0xFF)) & 0xFFFF
