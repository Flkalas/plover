pub const NOR_SIZE: usize = 128 * 1024;
pub const CW_FLASH_BASE: usize = 0x4000;

#[derive(Clone, Debug, Default)]
pub struct NorFlash {
    mem: Vec<u8>,
}

impl NorFlash {
    pub fn new() -> Self {
        Self {
            mem: vec![0xFF; NOR_SIZE],
        }
    }

    pub fn read(&self, flash_offset: usize) -> u8 {
        self.mem[flash_offset & (NOR_SIZE - 1)]
    }

    pub fn cpu_map_read(&self, cpu_addr: u16) -> u8 {
        let a = cpu_addr;
        if a < 0x0800 {
            return self.read(a as usize);
        }
        if a >= 0xFFFC {
            return self.read(a as usize);
        }
        0xFF
    }

    pub fn load_bytes(&mut self, data: &[u8], offset: usize) {
        for (i, &b) in data.iter().enumerate() {
            let idx = offset + i;
            if idx < NOR_SIZE {
                self.mem[idx] = b;
            }
        }
    }

    pub fn read_cw(&self, store_index: usize) -> u8 {
        self.read(CW_FLASH_BASE + (store_index & 0x7FF))
    }

    pub fn patch_cw_region(&mut self, words: &[u8], base: usize) {
        for (i, &w) in words.iter().enumerate() {
            let off = base + i;
            if off < NOR_SIZE {
                self.mem[off] = w;
            }
        }
    }

    pub fn load_hex_file(&mut self, path: &std::path::Path, offset: usize) {
        let data = crate::hex::load_hex(path, offset);
        self.load_bytes(&data, offset);
    }
}
