pub const MB_BASE: u16 = 0xFF00;

pub fn mmio_addr(offset: u8) -> u16 {
    MB_BASE | u16::from(offset)
}
