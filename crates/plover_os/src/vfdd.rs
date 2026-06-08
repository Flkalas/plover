use plover_copro::vfdd::{VirtualFdd, VfddError};

pub struct VfddDriver {
    dev: VirtualFdd,
}

impl VfddDriver {
    pub fn new(dev: VirtualFdd) -> Self {
        Self { dev }
    }

    pub fn read_sector(&self, n: usize) -> Result<Vec<u8>, VfddError> {
        self.dev.read_sector(n)
    }

    pub fn write_sector(&self, n: usize, data: &[u8]) -> Result<(), VfddError> {
        self.dev.write_sector(n, data)
    }
}
