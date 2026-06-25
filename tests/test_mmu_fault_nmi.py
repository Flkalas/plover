"""v1.1 MMU fault and /NMI."""

from hw.logic.mmu_v1_1 import Mmu71024State, PteEntry, decode_addr_v1_1, fault_from_pte


def test_fault_invalid():
    assert fault_from_pte(PteEntry(0, valid=False, we=True), cpu_wr=False)


def test_fault_readonly_write():
    assert fault_from_pte(PteEntry(1, valid=True, we=False), cpu_wr=True)
    assert not fault_from_pte(PteEntry(1, valid=True, we=False), cpu_wr=False)


def test_nmi_on_invalid_access():
    mmu = Mmu71024State()
    mmu.write_pte(2, PteEntry(pa_hi=2, valid=False, we=True))
    r = decode_addr_v1_1(0x2000, mmu, map_mode=1, cpu_wr=False)
    assert r.fault
    assert r.nmi


def test_nmi_on_ro_write():
    mmu = Mmu71024State()
    mmu.write_pte(3, PteEntry(pa_hi=3, valid=True, we=False))
    r = decode_addr_v1_1(0x3000, mmu, map_mode=1, cpu_wr=True)
    assert r.nmi


def test_no_nmi_on_valid_rw():
    mmu = Mmu71024State()
    mmu.write_pte(5, PteEntry(pa_hi=5, valid=True, we=True))
    r = decode_addr_v1_1(0x5000, mmu, map_mode=1, cpu_wr=True)
    assert not r.nmi
