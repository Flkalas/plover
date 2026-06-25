//! Plover v1.1 discrete MMU ??71024 PTE table + IS62 main RAM.

use crate::decode::{DecodeResult, MapDecoder};

pub const T_ACC_MMU_71024_NS: u32 = 15;
pub const T_ACC_MAIN_IS62_NS: u32 = 45;
pub const T_FAULT_COMB_NS: u32 = 5;
pub const T_MMU_PIPELINE_NS: u32 = T_ACC_MMU_71024_NS + T_ACC_MAIN_IS62_NS + T_FAULT_COMB_NS;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PteEntry {
    pub pa_hi: u8,
    pub valid: bool,
    pub we: bool,
}

impl PteEntry {
    pub fn pack(self) -> u8 {
        let mut v = self.pa_hi & 0xF;
        if self.valid {
            v |= 1 << 4;
        }
        if self.we {
            v |= 1 << 5;
        }
        v
    }

    pub fn unpack(byte: u8) -> Self {
        let b = byte & 0x3F;
        Self {
            pa_hi: b & 0xF,
            valid: (b & (1 << 4)) != 0,
            we: (b & (1 << 5)) != 0,
        }
    }
}

impl Default for PteEntry {
    fn default() -> Self {
        Self {
            pa_hi: 0,
            valid: true,
            we: true,
        }
    }
}

pub fn identity_pte_table() -> [PteEntry; 16] {
    std::array::from_fn(|i| PteEntry {
        pa_hi: i as u8,
        valid: true,
        we: true,
    })
}

#[derive(Clone, Debug)]
pub struct MmuV11 {
    pub pte: [PteEntry; 16],
}

impl Default for MmuV11 {
    fn default() -> Self {
        Self {
            pte: identity_pte_table(),
        }
    }
}

impl MmuV11 {
    pub fn read_pte(&self, va_page: u8) -> PteEntry {
        self.pte[(va_page & 0xF) as usize]
    }

    pub fn write_pte(&mut self, va_page: u8, entry: PteEntry) {
        self.pte[(va_page & 0xF) as usize] = entry;
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TranslateResult {
    pub va: u16,
    pub phys: u16,
    pub pte: PteEntry,
    pub fault: bool,
    pub fault_nmi: bool,
    pub mmu_bypass: bool,
    pub mem: DecodeResult,
}

fn needs_mmu(dec: &DecodeResult) -> bool {
    !dec.mailbox
        && !dec.force_fffc
        && !dec.rom_cpu
        && (dec.ram1 || dec.ram2)
}

pub fn fault_from_pte(pte: PteEntry, cpu_wr: bool) -> bool {
    if !pte.valid {
        return true;
    }
    cpu_wr && !pte.we
}

pub fn translate(
    mmu: &MmuV11,
    decoder: &MapDecoder,
    va: u16,
    map_mode: u8,
    reset_active: bool,
    cpu_wr: bool,
) -> TranslateResult {
    let mem = decoder.decode(va, map_mode, reset_active);
    if !needs_mmu(&mem) {
        return TranslateResult {
            va,
            phys: va,
            pte: PteEntry {
                pa_hi: ((va >> 12) & 0xF) as u8,
                valid: true,
                we: true,
            },
            fault: false,
            fault_nmi: false,
            mmu_bypass: true,
            mem,
        };
    }

    let pte = mmu.read_pte(((va >> 12) & 0xF) as u8);
    let fault = fault_from_pte(pte, cpu_wr);
    let phys = u16::from(pte.pa_hi & 0xF) << 12 | (va & 0x0FFF);
    let mem_phys = decoder.decode(phys, map_mode, reset_active);

    TranslateResult {
        va,
        phys,
        pte,
        fault,
        fault_nmi: fault,
        mmu_bypass: false,
        mem: mem_phys,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_map_roundtrip() {
        let mmu = MmuV11::default();
        let dec = MapDecoder;
        let r = translate(&mmu, &dec, 0x1234, 1, false, false);
        assert!(!r.fault);
        assert_eq!(r.phys, 0x1234);
    }

    #[test]
    fn invalid_pte_faults() {
        let mut mmu = MmuV11::default();
        mmu.write_pte(
            4,
            PteEntry {
                pa_hi: 4,
                valid: false,
                we: true,
            },
        );
        let dec = MapDecoder;
        let r = translate(&mmu, &dec, 0x4000, 1, false, false);
        assert!(r.fault_nmi);
    }
}
