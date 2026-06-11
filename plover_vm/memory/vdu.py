"""VDU/GFX state for Mailbox display commands (40×25 text + 320×200 RGB565)."""

from __future__ import annotations

from dataclasses import dataclass, field

# Text commands
CMD_VDU_CLS = 0x10
CMD_VDU_PUTCH = 0x11
CMD_VDU_GOTO = 0x12
CMD_VDU_ATTR = 0x13
CMD_VDU_PRINT = 0x14
CMD_VDU_SCROLL = 0x15
CMD_VDU_CURSORGET = 0x16
CMD_VDU_PAL_TEXT = 0x17

# Bitmap commands
CMD_GFX_CLS = 0x20
CMD_GFX_PLOT = 0x21
CMD_GFX_HLINE = 0x22
CMD_GFX_FILLRECT = 0x23
CMD_GFX_BLIT = 0x24
CMD_GFX_GETPIX = 0x25
CMD_GFX_TILE8 = 0x26
CMD_GFX_SET_TILE_PAL = 0x27
CMD_GFX_LAYER_CFG = 0x28
CMD_GFX_TILEMAP_SET = 0x29
CMD_GFX_OAM_WRITE = 0x2A
CMD_GFX_OAM_HIDE = 0x2B
CMD_GFX_FRAME_FLUSH = 0x2C
CMD_GFX_SPR_KEY = 0x2D

# System
CMD_VDU_VSYNC = 0x30
CMD_VDU_MODE = 0x31

VDU_COLS = 40
VDU_ROWS = 25
GFX_W = 320
GFX_H = 200

OAM_MAX = 32
LAYER_TILES_W = 40
LAYER_TILES_H = 25
LAYER_COUNT = 2

MODE_TEXT = 0
MODE_BITMAP = 1
MODE_BOTH = 2

DEFAULT_TEXT_PALETTE = (
    0x0000,  # 0 black
    0xF800,  # 1 red
    0x07E0,  # 2 green
    0xFFE0,  # 3 yellow
    0x001F,  # 4 blue
    0xF81F,  # 5 magenta
    0x07FF,  # 6 cyan
    0xFFFF,  # 7 white
    0x8410,  # 8 gray
    0xFC00,  # 9 orange
    0x0400,  # 10 dark green
    0x8010,  # 11 brown
    0x0010,  # 12 dark blue
    0x801F,  # 13 purple
    0x0410,  # 14 dark cyan
    0xC618,  # 15 light gray
)


@dataclass
class VduState:
    """Dual-layer display: text matrix + RGB565 bitmap."""

    chars: list[list[int]] = field(default_factory=lambda: [[0x20] * VDU_COLS for _ in range(VDU_ROWS)])
    attrs: list[list[int]] = field(default_factory=lambda: [[0x07] * VDU_COLS for _ in range(VDU_ROWS)])
    cursor_col: int = 0
    cursor_row: int = 0
    current_attr: int = 0x07
    text_palette: list[int] = field(default_factory=lambda: list(DEFAULT_TEXT_PALETTE))
    tile_palettes: list[list[int]] = field(default_factory=lambda: [list(DEFAULT_TEXT_PALETTE) for _ in range(16)])
    bitmap: list[int] = field(default_factory=lambda: [0x0000] * (GFX_W * GFX_H))
    mode: int = MODE_BOTH
    frame: int = 0
    last_error: bool = False
    layers: list[dict] = field(default_factory=lambda: [
        {"enabled": False, "scroll_x": 0, "scroll_y": 0, "tiles": [[0] * LAYER_TILES_W for _ in range(LAYER_TILES_H)]}
        for _ in range(LAYER_COUNT)
    ])
    oam: list[dict] = field(default_factory=lambda: [
        {"x": 0, "y": 0, "tile": 0, "pal": 0, "attr": 0, "flags": 0} for _ in range(OAM_MAX)
    ])
    sprite_transparent_nib: int = 0

    def reset_error(self) -> None:
        self.last_error = False

    def set_error(self) -> None:
        self.last_error = True

    def _rgb565_from_buf(self, buf: bytearray | bytes, off: int = 0) -> int:
        lo = buf[off] if off < len(buf) else 0
        hi = buf[off + 1] if off + 1 < len(buf) else 0
        return lo | (hi << 8)

    def _write_rgb565_to_buf(self, buf: bytearray, color: int, off: int = 0) -> None:
        if off < len(buf):
            buf[off] = color & 0xFF
        if off + 1 < len(buf):
            buf[off + 1] = (color >> 8) & 0xFF

    def _in_text_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < VDU_COLS and 0 <= row < VDU_ROWS

    def _in_gfx_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < GFX_W and 0 <= y < GFX_H

    def _set_pixel(self, x: int, y: int, color: int) -> None:
        if self._in_gfx_bounds(x, y):
            self.bitmap[y * GFX_W + x] = color & 0xFFFF

    def _get_pixel(self, x: int, y: int) -> int:
        if not self._in_gfx_bounds(x, y):
            return 0
        return self.bitmap[y * GFX_W + x] & 0xFFFF

    def _put_at_cursor(self, ch: int) -> None:
        if ch == 0x0A:  # LF
            self.cursor_col = 0
            self.cursor_row += 1
            if self.cursor_row >= VDU_ROWS:
                self._scroll_up(1)
            return
        if ch == 0x0D:  # CR
            self.cursor_col = 0
            return
        self.chars[self.cursor_row][self.cursor_col] = ch & 0xFF
        self.attrs[self.cursor_row][self.cursor_col] = self.current_attr & 0xFF
        self.cursor_col += 1
        if self.cursor_col >= VDU_COLS:
            self.cursor_col = 0
            self.cursor_row += 1
            if self.cursor_row >= VDU_ROWS:
                self._scroll_up(1)

    def _scroll_up(self, lines: int) -> None:
        n = max(0, min(lines, VDU_ROWS))
        if n == 0:
            return
        for r in range(n, VDU_ROWS):
            src = r
            dst = r - n
            self.chars[dst] = list(self.chars[src])
            self.attrs[dst] = list(self.attrs[src])
        for r in range(VDU_ROWS - n, VDU_ROWS):
            self.chars[r] = [0x20] * VDU_COLS
            self.attrs[r] = [self.current_attr & 0xFF] * VDU_COLS
        self.cursor_row = min(self.cursor_row, VDU_ROWS - 1)

    def _stamp_solid_tile(self, dst_x: int, dst_y: int, tile_id: int, pal_idx: int) -> None:
        if tile_id == 0:
            return
        palette = self.tile_palettes[pal_idx & 0x0F]
        nib = tile_id & 0x0F
        if nib == self.sprite_transparent_nib:
            return
        color = palette[nib]
        for ty in range(8):
            for tx in range(8):
                self._set_pixel(dst_x + tx, dst_y + ty, color)

    def _draw_layer(self, layer_idx: int) -> None:
        layer = self.layers[layer_idx]
        if not layer["enabled"]:
            return
        pal = layer_idx & 0x0F
        sx, sy = layer["scroll_x"], layer["scroll_y"]
        for ty in range(LAYER_TILES_H):
            for tx in range(LAYER_TILES_W):
                tile_id = layer["tiles"][ty][tx]
                if tile_id == 0:
                    continue
                px = tx * 8 - sx
                py = ty * 8 - sy
                if px >= GFX_W or py >= GFX_H or px <= -8 or py <= -8:
                    continue
                self._stamp_solid_tile(px, py, tile_id, pal)

    def _frame_flush(self) -> None:
        self.bitmap = [0x0000] * (GFX_W * GFX_H)
        self._draw_layer(0)
        self._draw_layer(1)
        for entry in self.oam:
            if entry["flags"] & 0x01 and entry["tile"] != 0:
                self._stamp_solid_tile(entry["x"], entry["y"], entry["tile"], entry["pal"])
        self.frame += 1

    def dispatch(self, cmd: int, param: int, aux: int, buffer: bytearray) -> None:
        """Execute one VDU/GFX command. Sets last_error on invalid args."""
        self.reset_error()
        p = param & 0xFF
        a = aux & 0xFF

        if cmd == CMD_VDU_CLS:
            fill = p
            for r in range(VDU_ROWS):
                self.chars[r] = [0x20] * VDU_COLS
                self.attrs[r] = [fill] * VDU_COLS
            self.cursor_col = 0
            self.cursor_row = 0
            return

        if cmd == CMD_VDU_PUTCH:
            self._put_at_cursor(p)
            return

        if cmd == CMD_VDU_GOTO:
            col, row = p, a
            if not self._in_text_bounds(col, row):
                self.set_error()
                return
            self.cursor_col = col
            self.cursor_row = row
            return

        if cmd == CMD_VDU_ATTR:
            self.current_attr = p
            return

        if cmd == CMD_VDU_PRINT:
            length = min(p, len(buffer))
            for i in range(length):
                self._put_at_cursor(buffer[i])
            return

        if cmd == CMD_VDU_SCROLL:
            self._scroll_up(p)
            return

        if cmd == CMD_VDU_CURSORGET:
            if len(buffer) >= 3:
                buffer[0] = self.cursor_col & 0xFF
                buffer[1] = self.cursor_row & 0xFF
                buffer[2] = self.current_attr & 0xFF
            return

        if cmd == CMD_VDU_PAL_TEXT:
            idx = p & 0x0F
            self.text_palette[idx] = self._rgb565_from_buf(buffer, 0) & 0xFFFF
            return

        if cmd == CMD_GFX_CLS:
            color = self._rgb565_from_buf(buffer, 0)
            self.bitmap = [color] * (GFX_W * GFX_H)
            return

        if cmd == CMD_GFX_PLOT:
            if len(buffer) < 4:
                self.set_error()
                return
            x, y = buffer[0], buffer[1]
            color = self._rgb565_from_buf(buffer, 2)
            if not self._in_gfx_bounds(x, y):
                self.set_error()
                return
            self._set_pixel(x, y, color)
            return

        if cmd == CMD_GFX_HLINE:
            if len(buffer) < 5:
                self.set_error()
                return
            x0, y, x1 = buffer[0], buffer[1], buffer[2]
            color = self._rgb565_from_buf(buffer, 3)
            if not self._in_gfx_bounds(x0, y) or not self._in_gfx_bounds(x1, y):
                self.set_error()
                return
            if x0 > x1:
                x0, x1 = x1, x0
            for x in range(x0, x1 + 1):
                self._set_pixel(x, y, color)
            return

        if cmd == CMD_GFX_FILLRECT:
            if len(buffer) < 7:
                self.set_error()
                return
            x, y, w, h = buffer[0], buffer[1], buffer[2], buffer[3]
            color = self._rgb565_from_buf(buffer, 4)
            if w == 0 or h == 0:
                return
            for dy in range(h):
                for dx in range(w):
                    self._set_pixel(x + dx, y + dy, color)
            return

        if cmd == CMD_GFX_BLIT:
            byte_len = p
            if len(buffer) < 2 or byte_len < 2:
                self.set_error()
                return
            x0, y0 = buffer[0], buffer[1]
            payload = buffer[2 : 2 + byte_len - 2]
            if len(payload) % 2 != 0:
                self.set_error()
                return
            px = 0
            for i in range(0, len(payload), 2):
                color = payload[i] | (payload[i + 1] << 8)
                self._set_pixel(x0 + px, y0, color)
                px += 1
            return

        if cmd == CMD_GFX_GETPIX:
            if len(buffer) < 2:
                self.set_error()
                return
            x, y = buffer[0], buffer[1]
            color = self._get_pixel(x, y)
            self._write_rgb565_to_buf(buffer, color, 2)
            return

        if cmd == CMD_GFX_TILE8:
            pal_idx = p & 0x0F
            if len(buffer) < 34:
                self.set_error()
                return
            dst_x, dst_y = buffer[0], buffer[1]
            tile = buffer[2:34]
            palette = self.tile_palettes[pal_idx]
            for ty in range(8):
                for tx in range(8):
                    byte_idx = ty * 4 + tx // 2
                    nib = (tile[byte_idx] >> (4 if tx & 1 else 0)) & 0x0F
                    if nib == self.sprite_transparent_nib:
                        continue
                    color = palette[nib]
                    self._set_pixel(dst_x + tx, dst_y + ty, color)
            return

        if cmd == CMD_GFX_SET_TILE_PAL:
            pal_idx = p & 0x0F
            entry = a & 0x0F
            self.tile_palettes[pal_idx][entry] = self._rgb565_from_buf(buffer, 0) & 0xFFFF
            return

        if cmd == CMD_GFX_LAYER_CFG:
            layer = p & 0x01
            if layer >= LAYER_COUNT:
                self.set_error()
                return
            self.layers[layer]["enabled"] = a != 0
            if len(buffer) >= 2:
                self.layers[layer]["scroll_x"] = buffer[0]
                self.layers[layer]["scroll_y"] = buffer[1]
            return

        if cmd == CMD_GFX_TILEMAP_SET:
            layer = p & 0x01
            if layer >= LAYER_COUNT or len(buffer) < 2:
                self.set_error()
                return
            tx, ty, tile_id = a, buffer[0], buffer[1]
            if tx >= LAYER_TILES_W or ty >= LAYER_TILES_H:
                self.set_error()
                return
            self.layers[layer]["tiles"][ty][tx] = tile_id
            return

        if cmd == CMD_GFX_OAM_WRITE:
            sid = p & 0x1F
            if sid >= OAM_MAX or len(buffer) < 6:
                self.set_error()
                return
            self.oam[sid] = {
                "x": buffer[0],
                "y": buffer[1],
                "tile": buffer[2],
                "pal": buffer[3],
                "attr": buffer[4],
                "flags": buffer[5],
            }
            return

        if cmd == CMD_GFX_OAM_HIDE:
            sid = p & 0x1F
            if sid >= OAM_MAX:
                self.set_error()
                return
            self.oam[sid]["flags"] &= ~0x01
            return

        if cmd == CMD_GFX_FRAME_FLUSH:
            self._frame_flush()
            return

        if cmd == CMD_GFX_SPR_KEY:
            self.sprite_transparent_nib = p & 0x0F
            return

        if cmd == CMD_VDU_VSYNC:
            self.frame += 1
            return

        if cmd == CMD_VDU_MODE:
            if p not in (MODE_TEXT, MODE_BITMAP, MODE_BOTH):
                self.set_error()
                return
            self.mode = p
            return

        self.set_error()

    def compose_text(self) -> str:
        lines = []
        for r in range(VDU_ROWS):
            row = bytes(self.chars[r]).decode("ascii", errors="replace").rstrip()
            lines.append(row)
        return "\n".join(lines)

    def snapshot_bitmap(self) -> bytes:
        out = bytearray(GFX_W * GFX_H * 2)
        for i, color in enumerate(self.bitmap):
            out[i * 2] = color & 0xFF
            out[i * 2 + 1] = (color >> 8) & 0xFF
        return bytes(out)
