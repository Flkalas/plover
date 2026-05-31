"""Load hex byte images."""

from __future__ import annotations

from pathlib import Path


def load_hex(path: Path | str, offset: int = 0) -> tuple[bytearray, int]:
    """Load one hex byte per line into buffer at offset. Returns (buf, max_end)."""
    p = Path(path)
    data = bytearray()
    end = offset
    if not p.is_file():
        return data, end
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        addr = offset + i
        val = int(line, 16) & 0xFF
        need = addr + 1
        if len(data) < need:
            data.extend(b"\x00" * (need - len(data)))
        data[addr] = val
        end = max(end, need)
    return data, end


def load_hex_sparse(path: Path | str, size: int, base: int = 0) -> bytearray:
    """Load hex lines into fixed-size buffer at base offset."""
    buf = bytearray(size)
    chunk, _ = load_hex(path, base)
    for i, b in enumerate(chunk):
        if base + i < size:
            buf[base + i] = b
    return buf


def load_sram_program(path: Path | str) -> bytearray:
    """Load program bytes; pad to 64K backing store slice."""
    raw, _ = load_hex(path, 0)
    return raw
