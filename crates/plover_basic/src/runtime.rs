use plover_copro::apu::{CMD_APU_CH_SYNC, CMD_APU_NOTE_ON, CMD_APU_SET_CTRL};
use plover_copro::hid::CMD_HID_KEY_READ;
use plover_copro::vdu::{
    CMD_GFX_FRAME_FLUSH, CMD_GFX_LAYER_CFG, CMD_GFX_OAM_WRITE, CMD_GFX_SET_TILE_PAL,
    CMD_GFX_TILEMAP_SET, CMD_VDU_CLS, CMD_VDU_PRINT,
};
use plover_mmu::MemoryBus;

pub struct BasicRuntime<'a> {
    pub bus: &'a mut MemoryBus,
}

impl<'a> BasicRuntime<'a> {
    pub fn new(bus: &'a mut MemoryBus) -> Self {
        Self { bus }
    }

    pub fn cls(&mut self) {
        self.bus.mailbox.issue_vdu(CMD_VDU_CLS, 0x07, 0, None);
    }

    pub fn print_str(&mut self, s: &str) {
        let data = s.as_bytes();
        if data.is_empty() {
            return;
        }
        let chunk = &data[..data.len().min(248)];
        self.bus
            .mailbox
            .issue_vdu(CMD_VDU_PRINT, chunk.len() as u8, 0, Some(chunk));
    }

    pub fn inkey(&mut self) -> u8 {
        self.bus.mailbox.issue_hid(CMD_HID_KEY_READ, None);
        self.bus.read_cpu(0xFF04)
    }

    pub fn sprite_set(&mut self, id: u8, x: u8, y: u8, tile: u8, pal: u8) {
        let buf = [x, y, tile, pal, 0, 1];
        self.bus
            .mailbox
            .issue_vdu(CMD_GFX_OAM_WRITE, id & 0x1F, 0, Some(&buf));
    }

    pub fn draw(&mut self) {
        self.bus.mailbox.issue_vdu(CMD_GFX_FRAME_FLUSH, 0, 0, None);
    }

    pub fn sound(&mut self, ch: u8, period: u16, dur: u16) {
        let buf = [
            ch & 0x03,
            (period & 0xFF) as u8,
            (period >> 8) as u8,
            12,
            (dur & 0xFF) as u8,
            (dur >> 8) as u8,
        ];
        self.bus.mailbox.issue_apu(CMD_APU_NOTE_ON, 0, Some(&buf));
        self.bus.mailbox.issue_apu(CMD_APU_CH_SYNC, 0, None);
    }

    pub fn layer_scroll(&mut self, layer: u8, sx: u8, sy: u8) {
        self.bus
            .mailbox
            .issue_vdu(CMD_GFX_LAYER_CFG, layer & 1, 1, Some(&[sx, sy]));
    }

    pub fn tile_set(&mut self, layer: u8, tx: u8, ty: u8, tile_id: u8) {
        self.bus
            .mailbox
            .issue_vdu(CMD_GFX_TILEMAP_SET, layer & 1, tx, Some(&[ty, tile_id]));
    }

    pub fn set_tile_color(&mut self, pal: u8, entry: u8, color: u16) {
        self.bus.mailbox.issue_vdu(
            CMD_GFX_SET_TILE_PAL,
            pal & 0x0F,
            entry & 0x0F,
            Some(&[(color & 0xFF) as u8, (color >> 8) as u8]),
        );
    }

    pub fn apu_init(&mut self) {
        self.bus
            .mailbox
            .issue_apu(CMD_APU_SET_CTRL, 0, Some(&[15, 0]));
    }
}

pub fn period_for_hz(hz: u32) -> u16 {
    if hz == 0 {
        return 0;
    }
    (44_100 / (2 * hz)).min(0xFFFF) as u16
}
