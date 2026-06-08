#!/usr/bin/env python3
"""Generate boot ROM + RAM kernel hex fixtures for v0.1 JMP handoff."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "hw" / "fixtures" / "boot"
SW = ROOT / "hw" / "fixtures" / "sw"
SRAM = ROOT / "hw" / "fixtures" / "sram"

OP_LDIO = 0x08
OP_STA16 = 0x0F
COPY_BASE = 0x0120
COPY_COUNT = 248
RAM_KERNEL_BASE = 0x0800


def _assemble_file(path: Path) -> list[int]:
    from plover_asm.assemble import assemble_file

    return list(assemble_file(path).bytes)


def emit_copy_loop() -> list[int]:
    """Unrolled LDIO MB_BUFFER[i] -> STA16 $0800+i (boot block-copy primitive)."""
    out: list[int] = []
    for i in range(COPY_COUNT):
        mb_off = 0x04 + i
        if mb_off > 0xFB:
            break
        dest = RAM_KERNEL_BASE + i
        out.extend([OP_LDIO, mb_off & 0xFF])
        out.extend([OP_STA16, dest & 0xFF, (dest >> 8) & 0xFF])
    out.extend([0x05, 0x00, 0x06])  # JMP sanitize @ $0600
    return out


def _patch_jmp(rom: list[int], addr: int, target: int) -> None:
    rom[addr] = 0x05
    rom[addr + 1] = target & 0xFF
    rom[addr + 2] = (target >> 8) & 0xFF


def _place(rom: list[int], offset: int, data: list[int]) -> None:
    for i, b in enumerate(data):
        if offset + i < len(rom):
            rom[offset + i] = b


def build_boot_rom() -> list[int]:
    rom = [0x00] * 0x800
    head = _assemble_file(SW / "boot_rom_head.pls")
    tail = _assemble_file(SW / "boot_rom_tail.pls")
    _place(rom, 0x0000, head)
    _place(rom, 0x0600, tail)

    copy = emit_copy_loop()
    end = COPY_BASE + len(copy)
    if end > 0x600:
        raise RuntimeError(f"copy loop overflows sanitize region: ends 0x{end:X}")
    _place(rom, COPY_BASE, copy)

    _patch_jmp(rom, 0x0000, 0x0100)
    # ROM constants @ $00F0 — reachable via 8-bit LDA (tools/gen_boot_fixtures.py)
    rom[0xF0] = 0x00
    rom[0xF1] = 0x01  # CMD_READ
    rom[0xF2] = 0x01  # ST_READY mask
    rom[0xF3] = 0xE0  # SP hi
    rom[0xF4] = 0xF6  # RP hi

    return rom


def build_manual_rom() -> list[int]:
    rom = [0x00] * 0x800
    core = _assemble_file(SW / "boot_rom_manual.pls")
    for i, b in enumerate(core):
        rom[i] = b
    _patch_jmp(rom, 0x0000, 0x0100)
    return rom


def write_hex(path: Path, data: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{b:02X}" for b in data) + "\n", encoding="utf-8")


def write_boot() -> None:
    write_hex(OUT / "boot_rom.hex", build_boot_rom())
    write_hex(OUT / "boot_rom_manual.hex", build_manual_rom())
    vector = [0x00, 0x00, 0x00, 0x00]
    write_hex(OUT / "boot_vector.hex", vector)


def write_kernel() -> None:
    from plover_asm.assemble import assemble_file

    res = assemble_file(SW / "kernel_boot.pls")
    write_hex(SRAM / "kernel_boot.sram.hex", list(res.bytes))
    ram = [0x00] * 0x100
    for i, b in enumerate(res.bytes):
        if i < len(ram):
            ram[i] = b
    write_hex(OUT / "ram_kernel.hex", ram)


def main() -> None:
    write_boot()
    write_kernel()
    print(f"wrote {OUT} and {SRAM / 'kernel_boot.sram.hex'}")


if __name__ == "__main__":
    main()
