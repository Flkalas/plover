pub mod boot_handoff;
pub mod bus;
pub mod decode;
pub mod hex;
pub mod mmio;
pub mod nor;
pub mod ram;

pub use boot_handoff::simulate_sector_load;
pub use bus::MemoryBus;
pub use mmio::mmio_addr;
pub use nor::CW_FLASH_BASE;
pub use plover_copro::mailbox::{
    MB_BUFFER, MB_CMD, MB_PARAM, MB_STATUS, ST_APU_READY, ST_HID_KEY_PENDING, ST_HID_MOUSE_PENDING,
};
