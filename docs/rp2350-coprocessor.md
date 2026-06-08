# RP2350 Coprocessor v0.1

**Device:** RP2350B (separate module/board)  
**Related:** [mailbox-protocol.md](mailbox-protocol.md)

---

## 1. Role

| Function | Description |
|----------|-------------|
| **VDU** | 40×25 text, 320×240@30 → 640×480@60 HDMI — [display-console.md](display-console.md) |
| **HID** | Keyboard/mouse events → Mailbox |
| **vFDD** | Virtual floppy — sector read/write for boot and OS |

CPU remains **master** for program execution; RP2350 serves MMIO Mailbox only (no IRQ).

---

## 2. Electrical

| Path | Part |
|------|------|
| Data CPU ↔ RP2350 | **SN74LVC8T245** (5 V 빵판 CPU만) · PCB 통합 시 **직접 3.3 V** — [BOM-3v3.md](../BOM-3v3.md) |
| Address/control | Phase-interleaved per [cpld-system-controller.md](cpld-system-controller.md) |
| Power | **AMS1117-3.3** for RP2350 rail |

---

## 3. Firmware stub

Reference implementation: [`firmware/rp2350/mailbox_stub/main.c`](../firmware/rp2350/mailbox_stub/main.c)

- Polls `MB_CMD` when CPU writes command.
- READ: load 512 B from SD → `MB_BUFFER` (chunked), set DataReady.
- WRITE: reverse path.
- GPU/HID: stub loops set status bits for hwsim bring-up.
- VDU target: [display-console.md](display-console.md) (firmware TBD).

---

## 4. Timing

- RP2350 responds within deterministic **Busy** window; CPU spins on `MB_STATUS`.
- No address snoop required if all I/O goes through Mailbox.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | Mailbox-centric copro contract |
