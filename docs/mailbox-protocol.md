# Mailbox Protocol v0.1

**Base address:** `$FF00` · **Span:** 252 bytes (`$FF00 – $FFFB`)  
**Related:** [rp2350-coprocessor.md](rp2350-coprocessor.md)

Polling only — **no IRQ**.

---

## 1. Register map

| Offset | Name | R/W | Description |
|--------|------|-----|-------------|
| `$FF00` | `MB_STATUS` | R | Bit0 **DataReady** · Bit1 **Busy** · Bit2 **Error** |
| `$FF01` | `MB_CMD` | W | Command to RP2350 |
| `$FF02` | `MB_PARAM` | W | Parameter (e.g. sector LSB) |
| `$FF03` | *(reserved)* | — | Future |
| `$FF04–$FFFB` | `MB_BUFFER` | R/W | **248-byte** payload |

512-byte virtual sectors use **multi-transfer** (2×248 + 16 bytes in reserved/param extension — TBD in copro firmware).

---

## 2. Commands (`MB_CMD`)

| Value | Name | Action |
|-------|------|--------|
| `0x00` | NOP | No operation |
| `0x01` | READ | Read sector `MB_PARAM` → fill buffer |
| `0x02` | WRITE | Write buffer → sector `MB_PARAM` |

---

## 3. CPU poll sequence

```asm
; Minimal poll loop (conceptual)
poll:
    LDA  $FF00          ; MB_STATUS
    AND  #$01           ; DataReady
    BEQ  poll
    LDA  $FF01          ; handle CMD / read buffer...
```

Full OS loop: interleave poll with main scheduler — see `hw/fixtures/sw/monitor_poll.asm`.

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
