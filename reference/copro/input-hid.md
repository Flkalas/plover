# Input HID v0.1 (keyboard / mouse)

**Related:** [mailbox-protocol.md](mailbox-protocol.md) · [rp2350-coprocessor.md](rp2350-coprocessor.md)

Normative **keyboard FIFO + mouse event queue** on RP2350 Core0. CPU reads input **only via Mailbox** (`MB_CMD` `0x40–0x43`); no input buffers on the 64 KiB CPU map. USB/TinyUSB must **not** inject into SRAM `0x7FEx`.

---

## 1. Architecture

| Item | Value |
|------|-------|
| Keyboard | **ASCII byte** queue (USB scan→ASCII on copro) |
| Mouse | **buttons** (bit0=L, bit1=R, bit2=M) + **dx/dy** signed int8 |
| Key queue depth | **64** |
| Mouse queue depth | **32** |
| Overflow | **Drop oldest** entry |
| Control | Mailbox only — **reject** SRAM `0x7FEx` scan model |
| Polling | **No IRQ** — `MB_STATUS` bits + READ commands |

---

## 2. RP2350 responsibilities

| Task | Core | Notes |
|------|------|-------|
| USB HID host (TinyUSB) | **Core0** | Keyboard/mouse report parse → enqueue |
| FIFO queues | Core0 | ≤ key 64 + mouse 32 events in RP2350 SRAM |
| VDU / HSTX | Core1 | No USB on Core1 |

**v0.1 constraint:** During vFDD **Busy**, HID Mailbox commands are **silent dropped** (same as APU).

---

## 3. Error policy (HID-specific)

Like APU, HID uses **silent drop** for busy/invalid inject — **no `ST_ERROR`**.

- Empty queue on READ → buffer bytes **zero**
- Invalid `HID_INJECT` payload → command ignored
- Poll **`HID_KEY_PENDING`** / **`HID_MOUSE_PENDING`** (MB_STATUS bit4/5) before READ (optional)

---

## 4. Mailbox commands

See [mailbox-protocol.md](mailbox-protocol.md) §2.5.

| CMD | Name | Summary |
|-----|------|---------|
| `0x40` | HID_POLL | Queue depths in buffer |
| `0x41` | HID_KEY_READ | Dequeue one ASCII key |
| `0x42` | HID_MOUSE_READ | Dequeue one mouse event |
| `0x43` | HID_INJECT | Enqueue test event (VM); copro-only on hardware |

**Reserved:** `0x44–0x4F` gamepad / extension.

---

## 5. VM / bring-up

| Layer | v0.1 |
|-------|------|
| logic VM (developer) | [`HidState`](../logic VM/memory/hid.py) — FIFO queues |
| Host USB | **Deferred** — `HID_INJECT` for tests |
| Forth | `KEY ( -- ch )`, `MOUSE? ( -- buttons dx dy )` |
| Discovery | `SIG_HID = 0x48` |
| Gate | `hid_smoke.pls` + VM queue assert |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-08 | v0.1 normative: keyboard/mouse FIFO, Mailbox 0x40–0x43 |
