use crate::MemoryBus;
use plover_copro::mailbox::{CMD_READ, MB_CMD, MB_PARAM};

pub const SP_CELL: u16 = 0x0E00;
pub const RP_CELL: u16 = 0x0F00;

pub fn simulate_sector_load(bus: &mut MemoryBus, image: &[u8], sector: u8) {
    let mut sector512 = [0u8; 512];
    let n = image.len().min(512);
    sector512[..n].copy_from_slice(&image[..n]);
    bus.mailbox.set_sector_stub(&sector512);
    bus.write_cpu(MB_PARAM, sector);
    bus.write_cpu(MB_CMD, CMD_READ);
}
