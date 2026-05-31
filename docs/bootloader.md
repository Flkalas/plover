# Bootloader v0.1

**Related:** [rom-architecture.md](rom-architecture.md) · [memory-map.md](memory-map.md)

---

## 1. Reset flow

1. `MAP_MODE=0` (Boot), `RESET_N` pulse.
2. CPLD forces fetch **`$FFFC`** → ROM vector → entry in **`$0000–$07FF`**.

---

## 2. Boot ROM responsibilities

| Step | Action |
|------|--------|
| POST | Minimal HW sanity (RAM spot check, mailbox ping) |
| vFDD | `MB_CMD=READ`, sector 0 → load kernel image via Mailbox |
| Copy | ROM utility + loaded sectors → **RAM `$0800+`** |
| Vector install | Write jump to `$0800` at **RAM** `$FFFC–$FFFF` (for Mode B) |
| Halt | Wait — **no** auto MAP_MODE switch |

---

## 3. Operator handoff

1. Flip DIP → **Run** (`MAP_MODE=1`).
2. Press **RESET**.
3. CPU fetches `$FFFC` from **RAM** → kernel @ `$0800`.

---

## 4. Fixtures

| File | Purpose |
|------|---------|
| `hw/fixtures/boot/boot_rom.hex` | 2 KB image + vector |
| `hw/fixtures/boot/ram_kernel.hex` | Expected RAM after copy |
| `hw/tests/v2_boot_handoff.yaml` | hwsim scenario (decode + vector check) |

---

## 5. Vector format

`$FFFC`: low byte of entry address  
`$FFFD`: high byte (same page or `$08` for `$0800`)

Mode A ROM vector @ `$FFFC` points to **`$0000`** or **`$0100`** boot entry.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | Manual Run + RESET handoff |
