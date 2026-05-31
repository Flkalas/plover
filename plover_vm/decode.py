"""v0.1 CPLD memory map decode (combinatorial, no timing)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecodeResult:
    mailbox: bool
    rom_cpu: bool
    ram1: bool
    ram2: bool
    force_fffc: bool


class MapDecoder:
    """Port of hwsim CpldSystemCtrl address decode."""

    def decode(self, addr: int, map_mode: int, reset_active: bool) -> DecodeResult:
        a = addr & 0xFFFF
        mb = 0xFF00 <= a <= 0xFFFB
        a15 = (a >> 15) & 1
        force = reset_active

        rom_en = False
        ram1_en = False
        ram2_en = False

        if not reset_active and not mb:
            if map_mode == 0:
                if a < 0x0800 or a >= 0xFFFC:
                    rom_en = True
                elif a15 == 0:
                    ram1_en = True
                else:
                    ram2_en = True
            else:
                if a15 == 0:
                    ram1_en = True
                else:
                    ram2_en = True

        return DecodeResult(
            mailbox=mb,
            rom_cpu=rom_en,
            ram1=ram1_en,
            ram2=ram2_en,
            force_fffc=force,
        )
