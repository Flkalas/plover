"""v1.1 MMU translate ??71024 PTE + IS62 main."""

from hw.logic.mmu_v1_1 import (
    Mmu71024State,
    PteEntry,
    decode_addr_v1_1,
    identity_pte_table,
)


def test_identity_map_passthrough():
    mmu = Mmu71024State()
    for va in (0x0800, 0x4000, 0x8100):
        r = decode_addr_v1_1(va, mmu, map_mode=1, cpu_wr=False)
        assert not r.fault
        assert r.phys == va
        assert not r.mmu_bypass


def test_mapped_page():
    mmu = Mmu71024State()
    mmu.write_pte(4, PteEntry(pa_hi=7, valid=True, we=True))
    r = decode_addr_v1_1(0x4000, mmu, map_mode=1)
    assert r.phys == 0x7000
    assert not r.fault


def test_rom_bypasses_mmu():
    mmu = Mmu71024State()
    mmu.write_pte(0, PteEntry(pa_hi=0xF, valid=False, we=False))
    r = decode_addr_v1_1(0x0100, mmu, map_mode=0)
    assert r.mmu_bypass
    assert not r.fault


def test_mailbox_bypasses_mmu():
    mmu = Mmu71024State()
    mmu.pte[0xF] = PteEntry(pa_hi=0, valid=False, we=False)
    r = decode_addr_v1_1(0xFF04, mmu, map_mode=1)
    assert r.mmu_bypass
    assert not r.fault


def test_pte_pack_unpack():
    e = PteEntry(pa_hi=0xA, valid=True, we=False)
    assert PteEntry.unpack(e.pack()) == e


def test_identity_table_has_16_entries():
    assert len(identity_pte_table()) == 16
