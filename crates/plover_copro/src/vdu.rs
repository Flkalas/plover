pub const CMD_VDU_CLS: u8 = 0x10;
pub const CMD_VDU_PUTCH: u8 = 0x11;
pub const CMD_VDU_GOTO: u8 = 0x12;
pub const CMD_VDU_ATTR: u8 = 0x13;
pub const CMD_VDU_PRINT: u8 = 0x14;
pub const CMD_VDU_SCROLL: u8 = 0x15;
pub const CMD_VDU_CURSORGET: u8 = 0x16;
pub const CMD_VDU_PAL_TEXT: u8 = 0x17;
pub const CMD_GFX_CLS: u8 = 0x20;
pub const CMD_GFX_PLOT: u8 = 0x21;
pub const CMD_GFX_HLINE: u8 = 0x22;
pub const CMD_GFX_FILLRECT: u8 = 0x23;
pub const CMD_GFX_BLIT: u8 = 0x24;
pub const CMD_GFX_GETPIX: u8 = 0x25;
pub const CMD_GFX_TILE8: u8 = 0x26;
pub const CMD_VDU_VSYNC: u8 = 0x30;
pub const CMD_VDU_MODE: u8 = 0x31;

pub const VDU_COLS: usize = 40;
pub const VDU_ROWS: usize = 25;
pub const GFX_W: usize = 320;
pub const GFX_H: usize = 200;

pub const MODE_TEXT: u8 = 0;
pub const MODE_BITMAP: u8 = 1;
pub const MODE_BOTH: u8 = 2;

pub const DEFAULT_TEXT_PALETTE: [u16; 16] = [
    0x0000, 0xF800, 0x07E0, 0xFFE0, 0x001F, 0xF81F, 0x07FF, 0xFFFF, 0x8410, 0xFC00, 0x0400,
    0x8010, 0x0010, 0x801F, 0x0410, 0xC618,
];

#[derive(Clone, Debug)]
pub struct VduState {
    pub chars: [[u8; VDU_COLS]; VDU_ROWS],
    pub attrs: [[u8; VDU_COLS]; VDU_ROWS],
    pub cursor_col: u8,
    pub cursor_row: u8,
    pub current_attr: u8,
    pub text_palette: [u16; 16],
    pub tile_palettes: [[u16; 16]; 16],
    pub bitmap: Vec<u16>,
    pub mode: u8,
    pub frame: u32,
    pub last_error: bool,
}

impl Default for VduState {
    fn default() -> Self {
        let chars = [[0x20u8; VDU_COLS]; VDU_ROWS];
        let attrs = [[0x07u8; VDU_COLS]; VDU_ROWS];
        Self {
            chars,
            attrs,
            cursor_col: 0,
            cursor_row: 0,
            current_attr: 0x07,
            text_palette: DEFAULT_TEXT_PALETTE,
            tile_palettes: [DEFAULT_TEXT_PALETTE; 16],
            bitmap: vec![0x0000; GFX_W * GFX_H],
            mode: MODE_BOTH,
            frame: 0,
            last_error: false,
        }
    }
}

impl VduState {
    pub fn compose_text(&self) -> String {
        let mut lines = Vec::with_capacity(VDU_ROWS);
        for row in &self.chars {
            let s: String = row.iter().map(|&c| c as char).collect();
            lines.push(s.trim_end().to_string());
        }
        lines.join("\n")
    }

    pub fn snapshot_bitmap(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(GFX_W * GFX_H * 2);
        for &color in &self.bitmap {
            out.push((color & 0xFF) as u8);
            out.push((color >> 8) as u8);
        }
        out
    }

    fn rgb565_from_buf(buffer: &[u8], off: usize) -> u16 {
        let lo = buffer.get(off).copied().unwrap_or(0);
        let hi = buffer.get(off + 1).copied().unwrap_or(0);
        u16::from(lo) | (u16::from(hi) << 8)
    }

    fn write_rgb565_to_buf(buffer: &mut [u8; 248], color: u16, off: usize) {
        if off < buffer.len() {
            buffer[off] = (color & 0xFF) as u8;
        }
        if off + 1 < buffer.len() {
            buffer[off + 1] = (color >> 8) as u8;
        }
    }

    fn in_text_bounds(&self, col: u8, row: u8) -> bool {
        (col as usize) < VDU_COLS && (row as usize) < VDU_ROWS
    }

    fn in_gfx_bounds(&self, x: u8, y: u8) -> bool {
        (x as usize) < GFX_W && (y as usize) < GFX_H
    }

    fn set_pixel(&mut self, x: u8, y: u8, color: u16) {
        if self.in_gfx_bounds(x, y) {
            self.bitmap[y as usize * GFX_W + x as usize] = color;
        }
    }

    fn get_pixel(&self, x: u8, y: u8) -> u16 {
        if !self.in_gfx_bounds(x, y) {
            return 0;
        }
        self.bitmap[y as usize * GFX_W + x as usize]
    }

    fn scroll_up(&mut self, lines: u8) {
        let n = lines.min(VDU_ROWS as u8) as usize;
        if n == 0 {
            return;
        }
        for r in n..VDU_ROWS {
            self.chars[r - n] = self.chars[r];
            self.attrs[r - n] = self.attrs[r];
        }
        for r in (VDU_ROWS - n)..VDU_ROWS {
            self.chars[r] = [0x20; VDU_COLS];
            self.attrs[r] = [self.current_attr; VDU_COLS];
        }
        self.cursor_row = self.cursor_row.min((VDU_ROWS - 1) as u8);
    }

    fn put_at_cursor(&mut self, ch: u8) {
        if ch == 0x0A {
            self.cursor_col = 0;
            self.cursor_row += 1;
            if self.cursor_row as usize >= VDU_ROWS {
                self.scroll_up(1);
            }
            return;
        }
        if ch == 0x0D {
            self.cursor_col = 0;
            return;
        }
        let row = self.cursor_row as usize;
        let col = self.cursor_col as usize;
        self.chars[row][col] = ch;
        self.attrs[row][col] = self.current_attr;
        self.cursor_col += 1;
        if self.cursor_col as usize >= VDU_COLS {
            self.cursor_col = 0;
            self.cursor_row += 1;
            if self.cursor_row as usize >= VDU_ROWS {
                self.scroll_up(1);
            }
        }
    }

    pub fn dispatch(&mut self, cmd: u8, param: u8, aux: u8, buffer: &mut [u8; 248]) {
        self.last_error = false;
        match cmd {
            CMD_VDU_CLS => {
                let fill = param;
                for r in 0..VDU_ROWS {
                    self.chars[r] = [0x20; VDU_COLS];
                    self.attrs[r] = [fill; VDU_COLS];
                }
                self.cursor_col = 0;
                self.cursor_row = 0;
            }
            CMD_VDU_PUTCH => self.put_at_cursor(param),
            CMD_VDU_GOTO => {
                if !self.in_text_bounds(param, aux) {
                    self.last_error = true;
                    return;
                }
                self.cursor_col = param;
                self.cursor_row = aux;
            }
            CMD_VDU_ATTR => self.current_attr = param,
            CMD_VDU_PRINT => {
                let length = (param as usize).min(buffer.len());
                for i in 0..length {
                    self.put_at_cursor(buffer[i]);
                }
            }
            CMD_VDU_SCROLL => self.scroll_up(param),
            CMD_VDU_CURSORGET => {
                buffer[0] = self.cursor_col;
                buffer[1] = self.cursor_row;
                buffer[2] = self.current_attr;
            }
            CMD_VDU_PAL_TEXT => {
                let idx = (param & 0x0F) as usize;
                self.text_palette[idx] = Self::rgb565_from_buf(buffer, 0);
            }
            CMD_GFX_CLS => {
                let color = Self::rgb565_from_buf(buffer, 0);
                self.bitmap.fill(color);
            }
            CMD_GFX_PLOT => {
                if buffer.len() < 4 {
                    self.last_error = true;
                    return;
                }
                let x = buffer[0];
                let y = buffer[1];
                let color = Self::rgb565_from_buf(buffer, 2);
                if !self.in_gfx_bounds(x, y) {
                    self.last_error = true;
                    return;
                }
                self.set_pixel(x, y, color);
            }
            CMD_GFX_HLINE => {
                if buffer.len() < 5 {
                    self.last_error = true;
                    return;
                }
                let mut x0 = buffer[0];
                let y = buffer[1];
                let mut x1 = buffer[2];
                let color = Self::rgb565_from_buf(buffer, 3);
                if !self.in_gfx_bounds(x0, y) || !self.in_gfx_bounds(x1, y) {
                    self.last_error = true;
                    return;
                }
                if x0 > x1 {
                    std::mem::swap(&mut x0, &mut x1);
                }
                for x in x0..=x1 {
                    self.set_pixel(x, y, color);
                }
            }
            CMD_GFX_FILLRECT => {
                if buffer.len() < 7 {
                    self.last_error = true;
                    return;
                }
                let x = buffer[0];
                let y = buffer[1];
                let w = buffer[2];
                let h = buffer[3];
                let color = Self::rgb565_from_buf(buffer, 4);
                if w == 0 || h == 0 {
                    return;
                }
                for dy in 0..h {
                    for dx in 0..w {
                        self.set_pixel(x.wrapping_add(dx), y.wrapping_add(dy), color);
                    }
                }
            }
            CMD_GFX_BLIT => {
                let byte_len = param as usize;
                if buffer.len() < 2 || byte_len < 2 {
                    self.last_error = true;
                    return;
                }
                let x0 = buffer[0];
                let y0 = buffer[1];
                let payload = &buffer[2..2 + byte_len.saturating_sub(2).min(buffer.len() - 2)];
                if payload.len() % 2 != 0 {
                    self.last_error = true;
                    return;
                }
                let mut px = 0u8;
                for i in (0..payload.len()).step_by(2) {
                    let color = u16::from(payload[i]) | (u16::from(payload[i + 1]) << 8);
                    self.set_pixel(x0.wrapping_add(px), y0, color);
                    px = px.wrapping_add(1);
                }
            }
            CMD_GFX_GETPIX => {
                if buffer.len() < 2 {
                    self.last_error = true;
                    return;
                }
                let color = self.get_pixel(buffer[0], buffer[1]);
                Self::write_rgb565_to_buf(buffer, color, 2);
            }
            CMD_GFX_TILE8 => {
                let pal_idx = (param & 0x0F) as usize;
                if buffer.len() < 34 {
                    self.last_error = true;
                    return;
                }
                let dst_x = buffer[0];
                let dst_y = buffer[1];
                let tile = &buffer[2..34];
                let palette = self.tile_palettes[pal_idx];
                for ty in 0..8u8 {
                    for tx in 0..8u8 {
                        let byte_idx = ty as usize * 4 + (tx as usize / 2);
                        let nib = if tx & 1 != 0 {
                            (tile[byte_idx] >> 4) & 0x0F
                        } else {
                            tile[byte_idx] & 0x0F
                        };
                        let color = palette[nib as usize];
                        self.set_pixel(dst_x.wrapping_add(tx), dst_y.wrapping_add(ty), color);
                    }
                }
            }
            CMD_VDU_VSYNC => self.frame += 1,
            CMD_VDU_MODE => {
                if param > MODE_BOTH {
                    self.last_error = true;
                } else {
                    self.mode = param;
                }
            }
            _ => self.last_error = true,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mailbox::{Mailbox, ST_ERROR, ST_READY};
    use crate::mailbox::MB_BUFFER;

    #[test]
    fn vdu_print_fillrect_vsync() {
        let mut vdu = VduState::default();
        let mut buf = [0u8; 248];
        vdu.dispatch(CMD_VDU_CLS, 0x07, 0, &mut buf);
        vdu.dispatch(CMD_VDU_PRINT, 5, 0, {
            buf[..5].copy_from_slice(b"HELLO");
            &mut buf
        });
        let rect = [10u8, 10, 4, 4, 0x00, 0xF8];
        buf[..6].copy_from_slice(&rect);
        vdu.dispatch(CMD_GFX_FILLRECT, 0, 0, &mut buf);
        vdu.dispatch(CMD_VDU_VSYNC, 0, 0, &mut buf);
        assert!(vdu.compose_text().contains('H'));
        assert_eq!(vdu.bitmap[10 * GFX_W + 10], 0xF800);
        assert_eq!(vdu.frame, 1);
    }

    #[test]
    fn vdu_cls_putch_wrap() {
        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_CLS, 0x1E, 0, None);
        assert_eq!(mb.vdu.chars[0][0], 0x20);
        assert_eq!(mb.vdu.attrs[0][0], 0x1E);
        mb.issue_vdu(CMD_VDU_PUTCH, b'A', 0, None);
        assert_eq!(mb.vdu.chars[0][0], b'A');
        mb.vdu.cursor_col = (VDU_COLS - 1) as u8;
        mb.issue_vdu(CMD_VDU_PUTCH, b'B', 0, None);
        assert_eq!(mb.vdu.chars[0][VDU_COLS - 1], b'B');
        assert_eq!(mb.vdu.cursor_col, 0);
        assert_eq!(mb.vdu.cursor_row, 1);
    }

    #[test]
    fn vdu_goto_error() {
        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_GOTO, 40, 0, None);
        assert_ne!(mb.status_byte() & ST_ERROR, 0);
        mb.issue_vdu(CMD_VDU_GOTO, 5, 10, None);
        assert_eq!(mb.vdu.cursor_col, 5);
        assert_eq!(mb.vdu.cursor_row, 10);
    }

    #[test]
    fn vdu_cursorget_via_mailbox() {
        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_GOTO, 3, 7, None);
        mb.issue_vdu(CMD_VDU_ATTR, 0x42, 0, None);
        mb.issue_vdu(CMD_VDU_CURSORGET, 0, 0, None);
        assert_eq!(mb.read(MB_BUFFER), 3);
        assert_eq!(mb.read(MB_BUFFER + 1), 7);
        assert_eq!(mb.read(MB_BUFFER + 2), 0x42);
        assert_ne!(mb.status_byte() & ST_READY, 0);
    }
}
