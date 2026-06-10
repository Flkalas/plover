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


@dataclass(frozen=True)
class GprDecodeTier2:
    reg_sel: int
    w_sel: int
    r_sel_a: int
    r_sel_b: int


def decode_ce_tier2(addr: int, map_mode: int, reset_active: bool) -> MemDecode:
    """CE via 74HC138×2 + 08/32/04 glue (Tier 2 breadboard).

    Structural path: CPLD mailbox/MAP qualifiers → 138 half-select + coarse Y*
    → glue → final /CE. Truth matches ``decode_addr`` (ideal CPLD-only Tier 0).
    """
    a = addr & 0xFFFF
    mb = 1 if 0xFF00 <= a <= 0xFFFB else 0
    a15 = (a >> 15) & 1
    a11 = (a >> 11) & 1
    fffc = 1 if reset_active else 0

    # 138 #2 half-select active when decode enabled (not mailbox, not reset force)
    decode_en = not mb and not fffc
    # 138 #1 CBA = A15,A14,A13 — region line within 64 KiB half
    _cba = ((a >> 13) & 7) if decode_en else 7

    rom_en = False
    ram1_en = False
    ram2_en = False
    if decode_en:
        if map_mode == 0:
            # Glue: MAP×A11 boot ROM window + vector enclave
            boot_rom = a < 0x0800
            vector_rom = a >= 0xFFFC
            if boot_rom or vector_rom:
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

    # Suppress unused — document 138/glue inputs used implicitly above
    _ = (a11, _cba)

    return MemDecode(
        mailbox_en=mb,
        ram1_cs_n=0 if ram1_en else 1,
        ram2_cs_n=0 if ram2_en else 1,
        rom_cs_n=0 if rom_en else 1,
        addr_force_fffc=fffc,
    )


def decode_gpr_tier2(opcode: int, phase: int, reg_we: int) -> GprDecodeTier2:
    """Legacy — Reg_Sel from opcode×phase PLA (archived v0.2)."""
    return decode_gpr_from_cw(reg_sel(opcode, phase), reg_we)


def decode_gpr_from_cw(reg_sel_val: int, reg_we: int) -> GprDecodeTier2:
    """v1.0 breadboard — REG_SEL[1:0] from latched CW (B9–B8)."""
    sel = reg_sel_val & 3
    we = 1 if reg_we else 0
    w_sel = sel if we else 0
    return GprDecodeTier2(
        reg_sel=sel,
        w_sel=w_sel & 3,
        r_sel_a=sel & 3,
        r_sel_b=sel & 3,
    )


def decode_ce_breadboard(addr: int, map_mode: int, reset_active: bool) -> MemDecode:
    """v1.0 — 138×2 + 08/32/04 glue truth (same as decode_ce_tier2)."""
    return decode_ce_tier2(addr, map_mode, reset_active)


def decode_gpr(opcode: int, phase: int, reg_we: int) -> GprDecode:
    sel = reg_sel(opcode, phase)
    loads = tuple(1 if (sel == r and reg_we) else 0 for r in range(4))
    return GprDecode(
        reg_sel=sel,
        reg_sel0=sel & 1,
        reg_sel1=(sel >> 1) & 1,
        load_r=loads,  # type: ignore[arg-type]
    )
