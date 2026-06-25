"""Plover v1.1 discrete MMU ??71024 PTE + IS62 main (sim / hwsim truth)."""

from __future__ import annotations

from dataclasses import dataclass, field

from hw.logic.cpld_decode import MemDecode, decode_addr

# Timing constants (ns) ??discrete-mmu-spec-v1.1.md
T_ACC_MMU_71024_NS = 15
T_ACC_MAIN_IS62_NS = 45
T_FAULT_COMB_NS = 5
T_MMU_PIPELINE_NS = T_ACC_MMU_71024_NS + T_ACC_MAIN_IS62_NS + T_FAULT_COMB_NS


@dataclass
class PteEntry:
    pa_hi: int  # PA[15:12], 4 bits
    valid: bool = True
    we: bool = True

    def pack(self) -> int:
        v = self.pa_hi & 0xF
        if self.valid:
            v |= 1 << 4
        if self.we:
            v |= 1 << 5
        return v & 0x3F

    @classmethod
    def unpack(cls, byte: int) -> PteEntry:
        b = byte & 0x3F
        return cls(
            pa_hi=b & 0xF,
            valid=bool(b & (1 << 4)),
            we=bool(b & (1 << 5)),
        )


def identity_pte_table() -> list[PteEntry]:
    """Boot handoff: VA page i maps to PA page i."""
    return [PteEntry(pa_hi=i, valid=True, we=True) for i in range(16)]


@dataclass
class Mmu71024State:
    """Behavioral 71024: 16 PTE bytes at A16=0; swap region not modeled in decode."""

    pte: list[PteEntry] = field(default_factory=identity_pte_table)

    def read_pte(self, va_page: int) -> PteEntry:
        return self.pte[va_page & 0xF]

    def write_pte(self, va_page: int, entry: PteEntry) -> None:
        self.pte[va_page & 0xF] = entry


@dataclass(frozen=True)
class MmuTranslateResult:
    va: int
    phys: int
    pte: PteEntry
    fault: bool
    nmi: bool
    mmu_bypass: bool
    mem: MemDecode


def _needs_mmu(va: int, map_mode: int, reset_active: bool) -> bool:
    """True when access is translated RAM (not ROM / mailbox / reset force)."""
    mem = decode_addr(va, map_mode, reset_active)
    if mem.mailbox_en or mem.addr_force_fffc:
        return False
    if mem.rom_cs_n == 0:
        return False
    if mem.ram1_cs_n == 0 or mem.ram2_cs_n == 0:
        return True
    return False


def fault_from_pte(pte: PteEntry, cpu_wr: bool) -> bool:
    if not pte.valid:
        return True
    if cpu_wr and not pte.we:
        return True
    return False


def translate_va(
    va: int,
    mmu: Mmu71024State,
    *,
    map_mode: int = 1,
    reset_active: bool = False,
    cpu_wr: bool = False,
) -> MmuTranslateResult:
    va &= 0xFFFF
    mem = decode_addr(va, map_mode, reset_active)
    bypass = not _needs_mmu(va, map_mode, reset_active)

    if bypass:
        return MmuTranslateResult(
            va=va,
            phys=va,
            pte=PteEntry(pa_hi=(va >> 12) & 0xF),
            fault=False,
            nmi=False,
            mmu_bypass=True,
            mem=mem,
        )

    pte = mmu.read_pte((va >> 12) & 0xF)
    fault = fault_from_pte(pte, cpu_wr)
    phys = ((pte.pa_hi & 0xF) << 12) | (va & 0xFFF)
    return MmuTranslateResult(
        va=va,
        phys=phys & 0xFFFF,
        pte=pte,
        fault=fault,
        nmi=fault,
        mmu_bypass=False,
        mem=decode_addr(phys, map_mode, reset_active),
    )


def decode_addr_v1_1(
    va: int,
    mmu: Mmu71024State,
    *,
    map_mode: int = 1,
    reset_active: bool = False,
    cpu_wr: bool = False,
) -> MmuTranslateResult:
    """Alias for translate_va ??v1.1 MMU decode entry point."""
    return translate_va(
        va, mmu, map_mode=map_mode, reset_active=reset_active, cpu_wr=cpu_wr
    )
