#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DecodeResult {
    pub mailbox: bool,
    pub rom_cpu: bool,
    pub ram1: bool,
    pub ram2: bool,
    pub force_fffc: bool,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct MapDecoder;

impl MapDecoder {
    pub fn decode(&self, addr: u16, map_mode: u8, reset_active: bool) -> DecodeResult {
        let a = addr;
        let mb = (0xFF00..=0xFFFB).contains(&a);
        let a15 = (a >> 15) & 1;
        let force = reset_active;

        let mut rom_en = false;
        let mut ram1_en = false;
        let mut ram2_en = false;

        if !reset_active && !mb {
            if map_mode == 0 {
                if a < 0x0800 || a >= 0xFFFC {
                    rom_en = true;
                } else if a15 == 0 {
                    ram1_en = true;
                } else {
                    ram2_en = true;
                }
            } else if a15 == 0 {
                ram1_en = true;
            } else {
                ram2_en = true;
            }
        }

        DecodeResult {
            mailbox: mb,
            rom_cpu: rom_en,
            ram1: ram1_en,
            ram2: ram2_en,
            force_fffc: force,
        }
    }
}
