# Bootloader v0.1

**Related:** [rom-architecture.md](rom-architecture.md) · [memory-map.md](../hardware/memory-map.md) · [boot-jmp-handoff.md](boot-jmp-handoff.md)

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
| Copy | ROM **block-copy** utility + loaded sectors → **RAM `$0800+`** |
| Pre-init | Zero GPR; write **SP/RP** at **`$0E00`/`$0F00`** — see [boot-jmp-handoff.md](boot-jmp-handoff.md) §5 |
| Vector install | Write jump to `$0800` at **RAM** `$FFFC–$FFFF` (for Mode B / recovery; block-copy) |
| Handoff | **HALT** (default bring-up) **or** **`JMP $0800`** ([boot-jmp-handoff.md](boot-jmp-handoff.md)) — **no** auto MAP_MODE switch |

---

## 2b. Stage1 bare-metal smoke (teaching gate)

Before kernel takeover, ROM may run a minimal GPIO smoke loop:

- Configure GPIO direction
- Poll switch input bit
- Toggle LED output bit

Reference: [baremetal-gpio-smoke.md](baremetal-gpio-smoke.md)

---

## 3. Operator handoff (recovery / warm boot)

Used when Boot ROM ends in **HALT**, or when **Run** map and RAM vector reset are required. Not needed if Boot ROM uses **JMP handoff** ([boot-jmp-handoff.md](boot-jmp-handoff.md)) for first entry.

1. Flip DIP → **Run** (`MAP_MODE=1`).
2. Press **RESET**.
3. CPU fetches `$FFFC` from **RAM** → kernel @ `$0800`.

---

## 4. Fixtures

| File | Purpose |
|------|---------|
| `hw/fixtures/boot/boot_rom.hex` | 2 KB image + vector |
| `hw/fixtures/boot/ram_kernel.hex` | Expected RAM after copy |
| `hw/tests/v2_boot_handoff.yaml` | pre-flight sim scenario (decode + vector check) |

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
| 2026-06-08 | JMP chain-load handoff; §5 init contract |
