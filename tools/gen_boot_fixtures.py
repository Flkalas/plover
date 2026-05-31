#!/usr/bin/env python3
"""Generate boot ROM + RAM kernel hex fixtures for v0.1 handoff sim."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "fixtures" / "boot"


def write_boot() -> None:
    """2 KB boot image @ CPU $0000–$07FF."""
    rom = [0xEA, 0x00] + [0x00] * (0x800 - 2)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "boot_rom.hex").write_text(
        "\n".join(f"{b:02X}" for b in rom) + "\n", encoding="utf-8"
    )
    vector = [0x00, 0x00, 0x00, 0x00]  # $FFFC -> $0000 (Mode A)
    (OUT / "boot_vector.hex").write_text(
        "\n".join(f"{b:02X}" for b in vector) + "\n", encoding="utf-8"
    )


def write_kernel() -> None:
    """RAM kernel stub @ $0800 for Mode B reset vector."""
    ram = [0x00] * 0x100
    entry = 0x0800
    ram[0x7C] = entry & 0xFF  # $FFFC low in image slice
    ram[0x7D] = (entry >> 8) & 0xFF
    ram[0x00] = 0xEA  # kernel entry NOP
    (OUT / "ram_kernel.hex").write_text(
        "\n".join(f"{b:02X}" for b in ram) + "\n", encoding="utf-8"
    )


def main() -> None:
    write_boot()
    write_kernel()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
