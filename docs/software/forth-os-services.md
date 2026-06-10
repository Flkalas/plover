# Forth OS services (S4)

Forth 위에 OS-like word를 추가해, 이후 subset C / 커널 계층에서 재사용할 I/O semantics를 고정한다.

## Block I/O (256B)

- `BLK@ (blk off -- byte)` : block `blk`의 byte offset 읽기
- `BLK! (byte blk off -- )` : block `blk`에 byte 쓰기
- `FLUSH ( -- )` : no-op (v0.1); S7에서 vFDD sector flush로 승격

## Console

Normative geometry: **40×25** — [display-console.md](../copro/display-console.md). VDU mailbox — [mailbox-protocol.md](../copro/mailbox-protocol.md) §2.1–2.3.

- `EMIT (ch -- )` : 출력 (host simulation; with `MemoryBus`, routes to VDU)
- `KEY ( -- ch)` : 입력 (with `MemoryBus`, HID_KEY_READ; else host `input_bytes`)

### VDU words (when `MemoryBus` attached)

| Word | Stack | Mailbox |
|------|-------|---------|
| `VCLS` | `( -- )` | VDU_CLS |
| `VPUT` | `( ch -- )` | VDU_PUTCH |
| `VGOTO` | `( col row -- )` | VDU_GOTO |
| `GPLOT` | `( x y color -- )` | GFX_PLOT (RGB565) |
| `GRECT` | `( x y w h color -- )` | GFX_FILLRECT |
| `GVSYNC` | `( -- )` | VDU_VSYNC |

## Input (when `MemoryBus` attached)

Normative HID — [input-hid.md](input-hid.md) · [mailbox-protocol.md](../copro/mailbox-protocol.md) §2.5.

| Word | Stack | Mailbox |
|------|-------|---------|
| `KEY` | `( -- ch )` | HID_KEY_READ; `0` if empty (falls back to host buffer) |
| `MOUSE?` | `( -- buttons dx dy )` | HID_MOUSE_READ; `0 0 0` if empty |

## Audio (when `MemoryBus` attached)

Normative PSG — [audio-apu.md](audio-apu.md) · [mailbox-protocol.md](../copro/mailbox-protocol.md) §2.4.

| Word | Stack | Mailbox |
|------|-------|---------|
| `BEEP` | `( period duration -- )` | APU ch0 square + SYNC; duration stored in VM state |

## Tests

- `tests/test_forth_blocks.py`

