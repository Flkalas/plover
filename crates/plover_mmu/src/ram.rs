pub const RAM_SIZE: usize = 64 * 1024;

#[derive(Clone, Debug, Default)]
pub struct Ram64K {
    mem: Vec<u8>,
}

impl Ram64K {
    pub fn new() -> Self {
        Self {
            mem: vec![0; RAM_SIZE],
        }
    }

    pub fn read(&self, addr: u16) -> u8 {
        self.mem[addr as usize]
    }

    pub fn write(&mut self, addr: u16, val: u8) {
        self.mem[addr as usize] = val;
    }

    pub fn load(&mut self, data: &[u8], base: u16) {
        for (i, &b) in data.iter().enumerate() {
            let addr = base.wrapping_add(i as u16);
            self.write(addr, b);
        }
    }

    pub fn nonzero_count(&self) -> usize {
        self.mem.iter().filter(|&&b| b != 0).count()
    }
}
