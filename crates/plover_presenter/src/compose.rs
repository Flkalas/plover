use crate::font8x8::FONT_8X8_BASIC;
use plover_copro::vdu::{GFX_H, GFX_W, MODE_BITMAP, MODE_BOTH, MODE_TEXT, VDU_COLS, VDU_ROWS, VduState};

pub const LOGICAL_W: usize = 320;
pub const LOGICAL_H: usize = 240;
pub const STATUS_H: usize = 20;
pub const OUTPUT_W: usize = 640;
pub const OUTPUT_H: usize = 480;

/// RGB888 buffer logical 320x240 (row-major).
pub fn compose_rgb(vdu: &VduState) -> Vec<u8> {
    let mut out = vec![0u8; LOGICAL_W * LOGICAL_H * 3];
    let show_bitmap = vdu.mode == MODE_BITMAP || vdu.mode == MODE_BOTH;
    let show_text = vdu.mode == MODE_TEXT || vdu.mode == MODE_BOTH;

    if show_bitmap {
        for y in 0..GFX_H {
            for x in 0..GFX_W {
                let c = vdu.bitmap[y * GFX_W + x];
                let (r, g, b) = rgb565_to_rgb(c);
                let idx = (y * LOGICAL_W + x) * 3;
                out[idx] = r;
                out[idx + 1] = g;
                out[idx + 2] = b;
            }
        }
    }

    if show_text {
        for row in 0..VDU_ROWS {
            for col in 0..VDU_COLS {
                let ch = vdu.chars[row][col];
                let attr = vdu.attrs[row][col];
                let fg_idx = attr & 0x0F;
                let bg_idx = (attr >> 4) & 0x0F;
                let fg = vdu.text_palette[fg_idx as usize];
                let bg = vdu.text_palette[bg_idx as usize];
                let (fr, fg_c, fb) = rgb565_to_rgb(fg);
                let (br, bg_c, bb) = rgb565_to_rgb(bg);
                for py in 0..8 {
                    for px in 0..8 {
                        let x = col * 8 + px;
                        let y = row * 8 + py;
                        if x >= LOGICAL_W || y >= GFX_H {
                            continue;
                        }
                        // Empty text cells leave the bitmap visible in MODE_BOTH.
                        if show_bitmap && vdu.mode == MODE_BOTH && ch == b' ' {
                            continue;
                        }
                        let glyph_on = simple_glyph_pixel(ch, px, py);
                        let transparent = show_bitmap && vdu.mode == MODE_BOTH && fg_idx == 0;
                        let (r, g, b) = if glyph_on {
                            if transparent {
                                continue;
                            }
                            (fr, fg_c, fb)
                        } else {
                            (br, bg_c, bb)
                        };
                        let idx = (y * LOGICAL_W + x) * 3;
                        out[idx] = r;
                        out[idx + 1] = g;
                        out[idx + 2] = b;
                    }
                }
            }
        }
    }

    // status bar 20px black
    for y in GFX_H..LOGICAL_H {
        for x in 0..LOGICAL_W {
            let idx = (y * LOGICAL_W + x) * 3;
            out[idx] = 0;
            out[idx + 1] = 0;
            out[idx + 2] = 0;
        }
    }
    out
}

pub fn upscale_nearest_2x(logical: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; OUTPUT_W * OUTPUT_H * 3];
    for y in 0..LOGICAL_H {
        for x in 0..LOGICAL_W {
            let src = (y * LOGICAL_W + x) * 3;
            let r = logical[src];
            let g = logical[src + 1];
            let b = logical[src + 2];
            for dy in 0..2 {
                for dx in 0..2 {
                    let ox = x * 2 + dx;
                    let oy = y * 2 + dy;
                    let dst = (oy * OUTPUT_W + ox) * 3;
                    out[dst] = r;
                    out[dst + 1] = g;
                    out[dst + 2] = b;
                }
            }
        }
    }
    out
}

fn rgb565_to_rgb(c: u16) -> (u8, u8, u8) {
    let r = (((c >> 11) & 0x1F) * 255 / 31) as u8;
    let g = (((c >> 5) & 0x3F) * 255 / 63) as u8;
    let b = ((c & 0x1F) * 255 / 31) as u8;
    (r, g, b)
}

fn simple_glyph_pixel(ch: u8, px: usize, py: usize) -> bool {
    let idx = ch as usize;
    if idx >= FONT_8X8_BASIC.len() {
        return false;
    }
    (FONT_8X8_BASIC[idx][py] >> px) & 1 != 0
}

#[cfg(test)]
mod tests {
    use super::*;
    use plover_copro::mailbox::Mailbox;
    use plover_copro::vdu::{CMD_VDU_MODE, CMD_VDU_PUTCH, MODE_BOTH};

    #[test]
    fn glyph_f_bar_on_left() {
        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_MODE, MODE_BOTH, 0, None);
        mb.issue_vdu(CMD_VDU_PUTCH, b'F', 0, None);
        let logical = compose_rgb(&mb.vdu);
        let left = fg_x_at(&logical, 0, 0);
        let right = fg_x_at(&logical, 0, 7);
        assert!(left < right, "F should not be mirrored (left={left} right={right})");
    }

    #[test]
    fn glyph_l_stem_on_left() {
        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_MODE, MODE_BOTH, 0, None);
        mb.issue_vdu(CMD_VDU_PUTCH, b'L', 0, None);
        let logical = compose_rgb(&mb.vdu);
        let left = fg_x_at(&logical, 0, 0);
        assert!(left <= 2, "L stem should be on the left (left={left})");
    }

    fn fg_x_at(logical: &[u8], col: usize, row: usize) -> usize {
        for px in 0..8 {
            let x = col * 8 + px;
            let y = row * 8;
            let idx = (y * LOGICAL_W + x) * 3;
            if logical[idx] > 200 {
                return px;
            }
        }
        8
    }

    #[test]
    fn mode_both_shows_bitmap_through_spaces() {
        use plover_copro::vdu::{CMD_GFX_FILLRECT, CMD_VDU_CLS, CMD_VDU_VSYNC, MODE_BOTH};

        let mut mb = Mailbox::default();
        mb.issue_vdu(CMD_VDU_MODE, MODE_BOTH, 0, None);
        mb.issue_vdu(CMD_VDU_CLS, 0x07, 0, None);
        mb.issue_vdu(
            CMD_GFX_FILLRECT,
            0,
            0,
            Some(&[10, 10, 8, 8, 0x00, 0xF8]),
        );
        mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);

        let logical = compose_rgb(&mb.vdu);
        let idx = (10 * LOGICAL_W + 10) * 3;
        assert!(
            logical[idx] > 200 && logical[idx + 1] < 20 && logical[idx + 2] < 20,
            "red fillrect should show through empty text cells"
        );
    }
}
