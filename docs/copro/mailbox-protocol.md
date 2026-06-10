# Mailbox Protocol v0.1

**Base address:** `$FF00` · **Span:** 252 bytes (`$FF00 – $FFFB`)  
**Related:** [rp2350-coprocessor.md](rp2350-coprocessor.md)

Polling only — **no IRQ**.

---

## 1. Register map

| Offset | Name | R/W | Description |
|--------|------|-----|-------------|
| `$FF00` | `MB_STATUS` | R | Bit0 **DataReady** · Bit1 **Busy** · Bit2 **Error** · Bit3 **APU_READY** · Bit4 **HID_KEY_PENDING** · Bit5 **HID_MOUSE_PENDING** |
| `$FF01` | `MB_CMD` | W | Command to RP2350 |
| `$FF02` | `MB_PARAM` | W | Parameter (e.g. sector LSB) |
| `$FF03` | `MB_AUX` | W | VDU/GFX sub-parameter (e.g. cursor row) |
| `$FF04–$FFFB` | `MB_BUFFER` | R/W | **248-byte** payload |

512-byte virtual sectors use **multi-transfer** (2×248 + 16 bytes in reserved/param extension — TBD in copro firmware).

---

## 2. Commands (`MB_CMD`)

| Value | Name | Action |
|-------|------|--------|
| `0x00` | NOP | No operation |
| `0x01` | READ | Read sector `MB_PARAM` → fill buffer |
| `0x02` | WRITE | Write buffer → sector `MB_PARAM` |

### 2.1 VDU / text (`0x10–0x17`)

See [display-console.md](display-console.md). CPU fills `MB_PARAM`, `MB_AUX`, and/or `MB_BUFFER`, then writes `MB_CMD`.

| Value | Name | PARAM | AUX / BUFFER | Action |
|-------|------|-------|--------------|--------|
| `0x10` | VDU_CLS | fill attr | — | Clear 40×25 text; cursor (0,0) |
| `0x11` | VDU_PUTCH | char | — | Write at cursor; advance; wrap at col 40 |
| `0x12` | VDU_GOTO | col | row | Set cursor |
| `0x13` | VDU_ATTR | attr | — | Default attr for PUTCH/PRINT (`fg:4 \| bg:4`) |
| `0x14` | VDU_PRINT | len | ascii[len] | Print len bytes (≤248) at cursor |
| `0x15` | VDU_SCROLL | lines | — | Scroll text up N lines |
| `0x16` | VDU_CURSORGET | — | out: col, row, attr | Read cursor state into buffer |
| `0x17` | VDU_PAL_TEXT | index 0–15 | RGB565 LE [0–1] | Set text palette entry |

### 2.2 GFX / bitmap (`0x20–0x26`)

Bitmap layer: **320×200**, RGB565. Coordinates in `MB_BUFFER`.

| Value | Name | PARAM | BUFFER | Action |
|-------|------|-------|--------|--------|
| `0x20` | GFX_CLS | — | color LE [0–1] | Fill bitmap |
| `0x21` | GFX_PLOT | — | x, y, c_lo, c_hi | Plot pixel |
| `0x22` | GFX_HLINE | — | x0, y, x1, c_lo, c_hi | Horizontal line |
| `0x23` | GFX_FILLRECT | — | x, y, w, h, c_lo, c_hi | Filled rectangle |
| `0x24` | GFX_BLIT | byte_len | x, y, RGB565… | Blit up to 123 pixels per transfer |
| `0x25` | GFX_GETPIX | — | in: x, y → out: c_lo, c_hi | Read pixel |
| `0x26` | GFX_TILE8 | pal_idx | dst_x, dst_y, tile[32] | Stamp 8×8 tile (4bpp palette indices) |

### 2.2.1 GFX console extensions v0.2 (`0x27–0x2D`)

Layer tilemaps: **40×25** cells (8×8 px). OAM: **32** sprites. See [game-api.md](game-api.md).

| Value | Name | PARAM | AUX / BUFFER | Action |
|-------|------|-------|--------------|--------|
| `0x27` | GFX_SET_TILE_PAL | pal_idx 0–15 | entry 0–15 | RGB565 LE [0–1] → `tile_palettes[pal][entry]` |
| `0x28` | GFX_LAYER_CFG | layer 0–1 | enable | scroll_x, scroll_y in BUFFER[0–1] |
| `0x29` | GFX_TILEMAP_SET | layer 0–1 | tile_x, tile_y | tile_id in BUFFER[0] (0=empty) |
| `0x2A` | GFX_OAM_WRITE | sprite_id 0–31 | — | x, y, tile, pal, attr, flags (bit0=visible) |
| `0x2B` | GFX_OAM_HIDE | sprite_id | — | Clear sprite visible flag |
| `0x2C` | GFX_FRAME_FLUSH | — | — | Draw layer0→layer1→OAM to bitmap; increment frame |
| `0x2D` | GFX_SPR_KEY | transparent_nib | — | 4bpp index skipped when stamping sprites |

**GFX_FRAME_FLUSH** draws enabled tile layers (scrolled), then visible OAM entries, using `tile_palettes`. Does not clear text layer.

### 2.3 System (`0x30–0x31`)

| Value | Name | PARAM | Action |
|-------|------|-------|--------|
| `0x30` | VDU_VSYNC | — | Frame flip complete → DataReady |
| `0x31` | VDU_MODE | mode | 0=text, 1=bitmap, 2=both (default 2) |

On **Error**, CPU issues `CMD_NOP` after handling. VDU/GFX commands use the same Busy → DataReady handshake as vFDD.

### 2.4 APU / PSG (`0x50–0x53`)

See [audio-apu.md](audio-apu.md). **Silent drop** on invalid/busy — no `ST_ERROR`.

| Value | Name | PARAM | BUFFER | Action |
|-------|------|-------|--------|--------|
| `0x50` | APU_SET_CTRL | — | `[0]` master vol 0–15, `[1]` flags bit0=mute | Global control |
| `0x51` | APU_CH_WRITE | — | ch, period LE, vol, wave | Stage channel (0–3) |
| `0x52` | APU_CH_SYNC | — | — | Apply staged channels |
| `0x53` | APU_CH_OFF | channel | — | Mute channel immediately |

**Wave:** `0`=off, `1`=square (ch0–2 only), `2`=noise (ch3 only).

**MB_STATUS bit3 `APU_READY`:** `1` when APU command queue accepts writes.

### 2.5 HID / input (`0x40–0x43`)

See [input-hid.md](input-hid.md). **Silent drop** on vFDD busy / invalid inject — no `ST_ERROR`.

| Value | Name | BUFFER | Action |
|-------|------|--------|--------|
| `0x40` | HID_POLL | out `[0]` key_depth, `[1]` mouse_depth | Queue depths (cap 255) |
| `0x41` | HID_KEY_READ | out `[0]` ASCII char; `0` if empty | Dequeue one key |
| `0x42` | HID_MOUSE_READ | out `[0]` buttons, `[1]` dx, `[2]` dy | Dequeue mouse; zeros if empty |
| `0x43` | HID_INJECT | `[0]` type: 0=key/`[1]` char, 1=mouse/`[1..3]` | Enqueue (VM/test; copro on hw) |

**MB_STATUS bit4 `HID_KEY_PENDING`:** keyboard queue non-empty.  
**MB_STATUS bit5 `HID_MOUSE_PENDING`:** mouse queue non-empty.

### 2.4.1 APU track extensions v0.2 (`0x54–0x57`)

Timed notes on PSG channels (tracks 0–3). **Silent drop** like §2.4.

| Value | Name | PARAM | BUFFER | Action |
|-------|------|-------|--------|--------|
| `0x54` | APU_NOTE_ON | — | ch, period LE, vol, dur_frames LE | Stage square wave; auto-off after dur |
| `0x55` | APU_NOTE_OFF | channel | — | Immediate channel mute |
| `0x56` | APU_TRACK_CLEAR | channel | — | Clear pending note timer |
| `0x57` | APU_SYNC | — | — | Alias of `0x52` APU_CH_SYNC |

Call `APU_SYNC` (`0x52` or `0x57`) after `APU_NOTE_ON` to hear the note. Copro decrements `dur_frames` each `mix_samples` batch.

**Reserved:** `0x44–0x4F` HID extension · `0x58–0x5F` PCM (future).

---

## 3. CPU poll sequence

```asm
; Minimal poll loop (normative LDIO offset encoding)
poll:
    LDIO $00            ; MB_STATUS @ $FF00
    CMP  $01            ; DataReady
    BEQ  ready
    JMP  poll
ready:
    LDIO $04            ; MB_BUFFER[0] @ $FF04
```

`LDIO` / `STIO` operand is **offset** from `$FF00` (not the full 16-bit address). Example: `STIO $01` → `$FF01` (`MB_CMD`).

Full OS loop: interleave poll with main scheduler — see `hw/fixtures/sw/monitor_poll.pls`.

---

## 4. RP2350 contract

- RP2350 firmware mirrors `MB_*` via shared buffer protocol.
- Sets **Busy** during SD/vFDD work; **DataReady** when CPU may consume buffer.
- **Error** on timeout or media fault — CPU clears by issuing NOP after handling.

---

## 5. Hardware decode

CPLD asserts `MAILBOX_EN` for `$FF00–$FFFB` only; RAM_2 `/CE` negated in this window.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | 252 B window; cmd 0/1/2 |
| 2026-06-08 | MB_AUX; VDU/GFX cmds 0x10–0x31 |
| 2026-06-08 | APU_READY bit3; PSG cmds 0x50–0x53 |
| 2026-06-08 | HID_KEY/MOUSE_PENDING bit4/5; HID cmds 0x40–0x43 |
| 2026-06-08 | GFX v0.2 layer/OAM 0x27–0x2D; APU NOTE_ON 0x54–0x57 |
