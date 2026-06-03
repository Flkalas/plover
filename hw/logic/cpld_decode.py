"""Ideal CPLD system decode (hwsim / cyclesim / MapDecoder truth source)."""

from __future__ import annotations

from dataclasses import dataclass

from hw.micro.reg_sel import reg_sel


@dataclass(frozen=True)
class MemDecode:
    mailbox_en: int
    ram1_cs_n: int
    ram2_cs_n: int
    rom_cs_n: int
    addr_force_fffc: int


@dataclass(frozen=True)
class GprDecode:
    reg_sel: int
    reg_sel0: int
    reg_sel1: int
    load_r: tuple[int, int, int, int]


def decode_addr(addr: int, map_mode: int, reset_active: bool) -> MemDecode:
    a = addr & 0xFFFF
    mb = 1 if 0xFF00 <= a <= 0xFFFB else 0
    a15 = (a >> 15) & 1
    fffc = 1 if reset_active else 0

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

    return MemDecode(
        mailbox_en=mb,
        ram1_cs_n=0 if ram1_en else 1,
        ram2_cs_n=0 if ram2_en else 1,
        rom_cs_n=0 if rom_en else 1,
        addr_force_fffc=fffc,
    )


def decode_gpr(opcode: int, phase: int, reg_we: int) -> GprDecode:
    sel = reg_sel(opcode, phase)
    loads = tuple(1 if (sel == r and reg_we) else 0 for r in range(4))
    return GprDecode(
        reg_sel=sel,
        reg_sel0=sel & 1,
        reg_sel1=(sel >> 1) & 1,
        load_r=loads,  # type: ignore[arg-type]
    )
