# Mailbox Protocol v0.1

**Base address:** `$FF00` · **Span:** 252 bytes (`$FF00 – $FFFB`)  
**Related:** [rp2350-coprocessor.md](rp2350-coprocessor.md)

Polling only — **no IRQ**.

---

## 1. Register map

| Offset | Name | R/W | Description |
|--------|------|-----|-------------|
| `$FF00` | `MB_STATUS` | R | Bit0 **DataReady** · Bit1 **Busy** · Bit2 **Error** · Bit3 **APU_READY** |
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

**Reserved:** `0x40–0x4F` HID · `0x54–0x5F` PCM (v0.2).

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
