# Plover v0.1 — System Architecture

**Version:** 0.1 · **Date:** 2026-06-01  
**Status:** Archived — Tier 0 bring-up (574×4 GPR + CPLD decode-only). Active: [system-architecture.md](../../system-architecture.md) v0.2.

Supersedes archived pre-v0.1 specs — see [archive/pre-v0.1/](archive/pre-v0.1/README.md).

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC) + **4×GPR (74HC574)** |
| **Control** | Microcoded — **8-bit CW** from single parallel NOR |
| **System CPLD** | **ATF1504AS** — decode, bus arb, timing, GPR `LOAD_*` (no GPR storage) |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot, utility, microcode table |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive CPLD:** reset vector and memory map use **combinatorial logic only** — no map/boot state registers inside CPLD.
- **ROM as law:** CPU executes; ROM holds boot, control tables, and fixed assets ([rom-architecture.md](rom-architecture.md)).
- **Logic VM:** [`plover_vm/`](../plover_vm/) — functional simulator with NOR/RAM/Mailbox for program bring-up ([hw-sim.md](hw-sim.md#plover-logic-vm-plover_vm)).

---

## 3. Block diagram

```
                    ┌── ATF1504AS (system_ctrl) ──┐
  4MHz ──÷2── 2MHz  │ decode · arb · LOAD_R*    │
                    └───┬──────┬──────┬─────────┘
                        │      │      │
    ┌───────────────────┘      │      └──────────────────┐
    ▼                          ▼                         ▼
 574×4 GPR                  2× SRAM                 SST39SF010A
 R0–R3                     64 KB                    boot+CW+utility
    │                          │                         │
    └──────── alu8 ────────────┴──────── MBR/PC ────────┘
                                      │
                              MMIO $FF00 ↔ RP2350B
```

---

## 4. Boot workflow

1. Power on — **MAP_MODE=Boot** (DIP default).
2. **RESET** — CPLD forces fetch @ **`$FFFC`** → ROM vector → boot @ `$0000–$07FF`.
3. Bootloader: POST → vFDD load (Mailbox) → copy kernel/utility to **RAM `$0800+`** → optional RAM vector @ `$FFFC` → **`JMP $0800`** (product) or **halt** (bring-up).
4. **Manual path only:** operator DIP → **Run**, press **RESET** → fetch `$FFFC` from **RAM** → kernel execute.

Details: [bootloader.md](bootloader.md) · [boot-jmp-handoff.md](boot-jmp-handoff.md) · [memory-map.md](memory-map.md).

---

## 5. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](memory-map.md) | Address map, Mode A/B |
| [rom-architecture.md](rom-architecture.md) | Control / Boot / Utility segments |
| [cpld-system-controller.md](cpld-system-controller.md) | CPLD ports, decode, GPR load |
| [hw-bringup/README.md](hw-bringup/README.md) | **M1–M5 breadboard bring-up index** |
| [hw-bringup-cpld-programming.md](hw-bringup-cpld-programming.md) | M2a detail — ATF1504 ISP |
| [hw-bringup-gpr-alu.md](hw-bringup-gpr-alu.md) | M2b detail — GPR ↔ ALU |
| [microcode-spec.md](microcode-spec.md) | 8b CW, ISA, Reg_Sel table |
| [mailbox-protocol.md](mailbox-protocol.md) | `$FF00` MMIO, polling |
| [rp2350-coprocessor.md](rp2350-coprocessor.md) | Copro board, firmware contract |
| [bootloader.md](bootloader.md) | ROM image, handoff |
| [alu-opcodes-timing.md](alu-opcodes-timing.md) | ALU comb delay (unchanged) |
| [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md) | **Breadboard target decided** — CPLD GPR, 138×2, no GAL; Tier 0–3, parasitics |

---

## 6. Verification

| Layer | Tool |
|-------|------|
| hwsim gate + ALU bringup | `python -m hwsim run --all` (15 tests) |
| Logic VM | `python -m pytest tests/ -q` |
| Microcode pack | `python tools/verify_control_store.py` |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | v0.1 baseline — GPR 574×4, single NOR, system CPLD |
