use crate::apu::{
    ApuState, CMD_APU_CH_OFF, CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, CMD_APU_SET_CTRL,
};
use crate::hid::{CMD_HID_INJECT, CMD_HID_KEY_READ, CMD_HID_MOUSE_READ, CMD_HID_POLL, HidState};
use crate::vdu::{
    CMD_GFX_BLIT, CMD_GFX_CLS, CMD_GFX_FILLRECT, CMD_GFX_GETPIX, CMD_GFX_HLINE, CMD_GFX_PLOT,
    CMD_GFX_TILE8, CMD_VDU_ATTR, CMD_VDU_CLS, CMD_VDU_CURSORGET, CMD_VDU_GOTO, CMD_VDU_MODE,
    CMD_VDU_PAL_TEXT, CMD_VDU_PRINT, CMD_VDU_PUTCH, CMD_VDU_SCROLL, CMD_VDU_VSYNC, VduState,
};

pub const MB_BASE: u16 = 0xFF00;
pub const MB_STATUS: u16 = 0xFF00;
pub const MB_CMD: u16 = 0xFF01;
pub const MB_PARAM: u16 = 0xFF02;
pub const MB_AUX: u16 = 0xFF03;
pub const MB_BUFFER: u16 = 0xFF04;

pub const CMD_NOP: u8 = 0x00;
pub const CMD_READ: u8 = 0x01;
pub const CMD_WRITE: u8 = 0x02;

pub const ST_READY: u8 = 0x01;
pub const ST_BUSY: u8 = 0x02;
pub const ST_ERROR: u8 = 0x04;
pub const ST_APU_READY: u8 = 0x08;
pub const ST_HID_KEY_PENDING: u8 = 0x10;
pub const ST_HID_MOUSE_PENDING: u8 = 0x20;

const VDU_CMDS: &[u8] = &[
    CMD_VDU_CLS,
    CMD_VDU_PUTCH,
    CMD_VDU_GOTO,
    CMD_VDU_ATTR,
    CMD_VDU_PRINT,
    CMD_VDU_SCROLL,
    CMD_VDU_CURSORGET,
    CMD_VDU_PAL_TEXT,
    CMD_GFX_CLS,
    CMD_GFX_PLOT,
    CMD_GFX_HLINE,
    CMD_GFX_FILLRECT,
    CMD_GFX_BLIT,
    CMD_GFX_GETPIX,
    CMD_GFX_TILE8,
    CMD_VDU_VSYNC,
    CMD_VDU_MODE,
];

const APU_CMDS: &[u8] = &[CMD_APU_SET_CTRL, CMD_APU_CH_WRITE, CMD_APU_CH_SYNC, CMD_APU_CH_OFF];

const HID_CMDS: &[u8] = &[CMD_HID_POLL, CMD_HID_KEY_READ, CMD_HID_MOUSE_READ, CMD_HID_INJECT];

#[derive(Clone, Debug)]
pub struct Mailbox {
    status: u8,
    cmd: u8,
    param: u8,
    aux: u8,
    buffer: [u8; 248],
    sector: [u8; 512],
    pub vdu: VduState,
    pub apu: ApuState,
    pub hid: HidState,
    apu_ready: bool,
    vfdd_busy: bool,
    hid_payload_len: u8,
}

impl Default for Mailbox {
    fn default() -> Self {
        Self {
            status: 0,
            cmd: 0,
            param: 0,
            aux: 0,
            buffer: [0; 248],
            sector: [0; 512],
            vdu: VduState::default(),
            apu: ApuState::default(),
            hid: HidState::default(),
            apu_ready: true,
            vfdd_busy: false,
            hid_payload_len: 0,
        }
    }
}

impl Mailbox {
    pub fn status_byte(&self) -> u8 {
        let mut base = self.status;
        if self.apu_ready {
            base |= ST_APU_READY;
        }
        if self.hid.key_pending() {
            base |= ST_HID_KEY_PENDING;
        }
        if self.hid.mouse_pending() {
            base |= ST_HID_MOUSE_PENDING;
        }
        base
    }

    pub fn read(&self, addr: u16) -> u8 {
        match addr {
            MB_STATUS => self.status_byte(),
            MB_CMD => self.cmd,
            MB_PARAM => self.param,
            MB_AUX => self.aux,
            a if (MB_BUFFER..=0xFFFB).contains(&a) => self.buffer[(a - MB_BUFFER) as usize],
            _ => 0xFF,
        }
    }

    pub fn write(&mut self, addr: u16, val: u8) {
        match addr {
            MB_CMD => {
                self.cmd = val;
                self.handle_cmd();
            }
            MB_PARAM => self.param = val,
            MB_AUX => self.aux = val,
            a if (MB_BUFFER..=0xFFFB).contains(&a) => {
                self.buffer[(a - MB_BUFFER) as usize] = val;
            }
            _ => {}
        }
    }

    pub fn issue_vdu(&mut self, cmd: u8, param: u8, aux: u8, buffer: Option<&[u8]>) {
        self.param = param;
        self.aux = aux;
        if let Some(b) = buffer {
            let n = b.len().min(248);
            self.buffer[..n].copy_from_slice(&b[..n]);
        }
        self.cmd = cmd;
        self.handle_cmd();
    }

    pub fn issue_apu(&mut self, cmd: u8, param: u8, buffer: Option<&[u8]>) {
        self.param = param;
        if let Some(b) = buffer {
            let n = b.len().min(248);
            self.buffer[..n].copy_from_slice(&b[..n]);
        }
        self.cmd = cmd;
        self.handle_cmd();
    }

    pub fn issue_hid(&mut self, cmd: u8, buffer: Option<&[u8]>) {
        self.hid_payload_len = buffer.map(|b| b.len().min(255) as u8).unwrap_or(0);
        if let Some(b) = buffer {
            let n = b.len().min(248);
            self.buffer[..n].copy_from_slice(&b[..n]);
        }
        self.cmd = cmd;
        self.handle_cmd();
    }

    pub fn set_sector_stub(&mut self, data: &[u8]) {
        let n = data.len().min(512);
        self.sector[..n].copy_from_slice(&data[..n]);
    }

    fn handle_apu(&mut self, cmd: u8) {
        if self.vfdd_busy || (self.status & ST_BUSY) != 0 {
            return;
        }
        if self.apu.dispatch(cmd, self.param, &mut self.buffer) {
            self.apu_ready = true;
        }
    }

    fn handle_hid(&mut self, cmd: u8) {
        if self.vfdd_busy || (self.status & ST_BUSY) != 0 {
            return;
        }
        let n = if self.hid_payload_len == 0 {
            248
        } else {
            self.hid_payload_len as usize
        };
        self.hid.dispatch(cmd, &mut self.buffer, n);
    }

    fn handle_cmd(&mut self) {
        let cmd = self.cmd;
        if cmd == CMD_NOP {
            return;
        }
        match cmd {
            CMD_READ => {
                self.vfdd_busy = true;
                self.status = ST_BUSY;
                let sector = self.param as usize;
                let start = sector * 512;
                let end = (start + 248).min(self.sector.len());
                self.buffer[..(end - start)].copy_from_slice(&self.sector[start..end]);
                self.vfdd_busy = false;
                self.status = ST_READY;
                self.cmd = CMD_NOP;
            }
            CMD_WRITE => {
                self.vfdd_busy = true;
                self.status = ST_BUSY;
                let sector = self.param as usize;
                let start = sector * 512;
                let n = 248.min(self.sector.len().saturating_sub(start));
                self.sector[start..start + n].copy_from_slice(&self.buffer[..n]);
                self.vfdd_busy = false;
                self.status = ST_READY;
                self.cmd = CMD_NOP;
            }
            c if HID_CMDS.contains(&c) => {
                self.handle_hid(c);
                self.cmd = CMD_NOP;
            }
            c if APU_CMDS.contains(&c) => {
                self.handle_apu(c);
                self.cmd = CMD_NOP;
            }
            c if VDU_CMDS.contains(&c) => {
                self.status = ST_BUSY;
                self.vdu.dispatch(c, self.param, self.aux, &mut self.buffer);
                if self.vdu.last_error {
                    self.status = ST_ERROR;
                } else {
                    self.status = ST_READY;
                }
                self.cmd = CMD_NOP;
            }
            _ => {
                self.status = ST_ERROR;
                self.cmd = CMD_NOP;
            }
        }
    }
}
