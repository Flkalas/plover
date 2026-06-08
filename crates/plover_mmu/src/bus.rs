use crate::decode::MapDecoder;
use crate::nor::NorFlash;
use crate::ram::Ram64K;
use plover_copro::Mailbox;

#[derive(Clone, Debug)]
pub struct MemoryBus {
    pub nor: NorFlash,
    pub ram: Ram64K,
    pub mailbox: Mailbox,
    decoder: MapDecoder,
    pub map_mode: u8,
    pub reset_active: bool,
}

impl Default for MemoryBus {
    fn default() -> Self {
        Self {
            nor: NorFlash::new(),
            ram: Ram64K::new(),
            mailbox: Mailbox::default(),
            decoder: MapDecoder,
            map_mode: 0,
            reset_active: false,
        }
    }
}

impl MemoryBus {
    pub fn fetch_addr(&self, pc: u16) -> u16 {
        if self.reset_active {
            0xFFFC
        } else {
            pc
        }
    }

    pub fn read_cpu(&self, addr: u16) -> u8 {
        let d = self.decoder.decode(addr, self.map_mode, self.reset_active);
        if d.mailbox {
            return self.mailbox.read(addr);
        }
        if d.rom_cpu {
            return self.nor.cpu_map_read(addr);
        }
        if d.ram1 || d.ram2 {
            return self.ram.read(addr);
        }
        0xFF
    }

    pub fn write_cpu(&mut self, addr: u16, val: u8) {
        let d = self.decoder.decode(addr, self.map_mode, self.reset_active);
        if d.mailbox {
            self.mailbox.write(addr, val);
            return;
        }
        if d.rom_cpu {
            return;
        }
        if d.ram1 || d.ram2 {
            self.ram.write(addr, val);
        }
    }
}
