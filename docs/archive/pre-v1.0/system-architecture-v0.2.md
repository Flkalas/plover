# Plover v0.2 — System Architecture

**Version:** 0.2 · **Date:** 2026-06-10  
**Status:** Active normative specification (Tier 2 breadboard)

Supersedes [v0.1 Tier 0 bring-up](archive/pre-v0.1/system-architecture-v0.1.md). Design rationale: [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md).

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC) + **4×GPR in ATF1504** |
| **Control** | Microcoded — **8-bit CW** from single parallel NOR |
| **System CPLD** | **ATF1504AS (100-TQFP)** — GPR FFs, Reg_Sel, mailbox/map glue |
| **CE decode** | **74HC138×2** + **74HC08/32/04** glue → RAM/ROM `/CE` |
| **Flags / branch** | **574×1 FLG** (Z/C) + **08/32** BEQ glue — **no GAL** |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot, utility, microcode table |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

**Legacy bring-up:** M1–M2b may use [Tier 0 574×4 path](hw-bringup/tier2-migration.md#tier-0-legacy).

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive CPLD:** reset vector and memory map use **combinatorial logic only** — no map/boot state registers inside CPLD.
- **ROM as law:** CPU executes; ROM holds boot, control tables, and fixed assets ([rom-architecture.md](rom-architecture.md)).
- **Logic VM:** [`plover_vm/`](../plover_vm/) — functional simulator with NOR/RAM/Mailbox for program bring-up ([hw-sim.md](../../simulation/hw-sim.md#plover-logic-vm-plover_vm)).

---

## 3. Block diagram

```text
                    ┌── ATF1504AS (GPR + decode glue) ──┐
  4MHz ──÷2── 2MHz  │ q_a/q_b · Reg_Sel · MAILBOX     │
                    └───┬──────────┬──────────┬─────────┘
                        │          │          │
    ┌───────────────────┘          │          └──────────────┐
    ▼                              ▼                         ▼
  alu8 ◄── q_a/q_b            74HC138×2 + glue          SST39SF010A
    │                         → 2× SRAM                  boot+CW
    │                              │
    └──────── MBR/PC (574) ────────┴── MMIO $FF00 ↔ RP2350B
         FLG (574×1)
```

---

## 4. Boot workflow

1. Power on — **MAP_MODE=Boot** (DIP default).
2. **RESET** — CPLD forces fetch @ **`$FFFC`** → ROM vector → boot @ `$0000–$07FF`.
3. Bootloader: POST → vFDD load (Mailbox) → copy kernel/utility to **RAM `$0800+`** → optional RAM vector @ `$FFFC` → **`JMP $0800`** (product) or **halt** (bring-up).
4. **Manual path only:** operator DIP → **Run**, press **RESET** → fetch `$FFFC` from **RAM** → kernel execute.

Details: [bootloader.md](../../boot/bootloader.md) · [boot-jmp-handoff.md](../../boot/boot-jmp-handoff.md) · [memory-map.md](../../hardware/memory-map.md).

---

## 5. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](../../hardware/memory-map.md) | Address map, 138×2 decode partition |
| [cpld-system-controller.md](cpld-system-controller.md) | CPLD ports, GPR, 138 enables |
| [archive/pre-v0.1/cpld-hybrid-v1.3.md](archive/pre-v0.1/cpld-hybrid-v1.3.md) | CPLD GPR port / timing reference |
| [hw-bringup/README.md](hw-bringup/README.md) | M1–M5 bring-up (Tier 0 legacy + Tier 2 migration) |
| [microcode-spec.md](microcode-spec.md) | 8b CW, ISA, Reg_Sel |
| [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md) | Decisions, parasitics, tiers |

---

## 6. Verification

| Layer | Tool |
|-------|------|
| hwsim (Tier 0 + Tier 2) | `python -m hwsim run --all` |
| Tier 2 gates | `cpld_regfile_dual_read`, `mem_decode_tier2`, `cpld_gpr_decode_tier2` |
| cyclesim | `python -m cyclesim run hw/tests/cyclesim/cpld_regfile_dual_read.yaml` |
| Logic VM | `python -m pytest tests/ -q` |
| CE parity | `pytest tests/test_cpld_decode_tier2.py` |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | v0.1 — 574×4 GPR, CPLD direct CS (archived) |
| 2026-06-10 | **v0.2** — CPLD GPR + 138×2 CE + 574 FLG; no GAL |
