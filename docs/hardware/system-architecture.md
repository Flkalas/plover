# Plover v1.0 — System Architecture

**Version:** 1.0 (pre-release) · **Date:** 2026-06-10  
**Status:** Active normative specification (breadboard)

Supersedes [v0.2](../archive/pre-v1.0/system-architecture-v0.2.md). Design rationale: [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md).

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC) + **4×GPR in ATF1504** |
| **Control** | Microcoded — **10-bit CW** from parallel NOR (`REG_SEL` in CW B9–B8) |
| **System CPLD** | **ATF1504AS-10JU44** (PLCC-44) — **GPR only** (~40 MC) |
| **CE decode** | **74HC138×2** + **74HC08/32/04** glue → RAM/ROM `/CE` |
| **Flags / branch** | **574×1 FLG** (Z/C) + **08/32** BEQ glue |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot, utility, microcode table |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive map:** mailbox/MAP qualifiers in **discrete gates**; CPLD holds GPR only.
- **ROM as law:** CPU executes; ROM holds boot, control tables, and fixed assets ([rom-architecture.md](rom-architecture.md)).
- **Logic VM:** [`plover_vm/`](../plover_vm/) — functional simulator ([hw-sim.md](../simulation/hw-sim.md#plover-logic-vm-plover_vm)).

---

## 3. Block diagram

```text
  Flash CW (10b) ──► 574 CW_L/CW_H ──┬── B7-B0 ──► 245 / MEM / Y_OE
                                    └── B9-B8 ──► CPLD GPR w_sel/r_sel

  A[15:0] ──► 08/32 mailbox·MAP ──► 74HC138×2 ──► /CE ──► SRAM×2 + SST39

  ATF1504 ── q_a/q_b ──► alu8 ◄── MBR/PC (574)
  FLG (574×1) ── BEQ glue ── 161
```

---

## 4. Boot workflow

1. Power on — **MAP_MODE=Boot** (DIP default).
2. **RESET** — fetch @ **`$FFFC`** (**74HC157** addr MUX) → ROM vector → boot @ `$0000–$07FF`.
3. Bootloader: POST → vFDD load (Mailbox) → copy kernel to **RAM `$0800+`** → **`JMP $0800`** or halt.
4. Operator DIP → **Run**, **RESET** → fetch `$FFFC` from **RAM**.

Details: [bootloader.md](../boot/bootloader.md) · [memory-map.md](memory-map.md).

---

## 5. Physical packages (v1.0 breadboard)

CPLD `ATF1504AS-10JU44` + PLCC→DIP (#15); Flash `SST39SF010A-70-4C-PHE` PDIP 직결; SRAM `IS62C256` + SOP28 (#3a)×2; `SN74LVC8T245` + SOIC-24 (#3c)×3. 상세: [parts-on-hand.md](../project/parts-on-hand.md).

---

## 6. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](memory-map.md) | Address map, 138×2 + gate decode |
| [cpld-system-controller.md](cpld-system-controller.md) | CPLD GPR ports (~40 MC) |
| [microcode-spec.md](microcode-spec.md) | 10b CW, ISA |
| [hw-bringup/README.md](../hw-bringup/README.md) | M1–M5 breadboard bring-up |
| [hw-bringup/breadboard-wiring.md](../hw-bringup/breadboard-wiring.md) | 138×2, gates, CW latch |
| [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md) | Decisions, parasitics |

---

## 7. Verification

| Layer | Tool |
|-------|------|
| hwsim | `python -m hwsim run --all` |
| Breadboard gates | `cpld_regfile_dual_read`, `mem_decode_breadboard`, `cpld_gpr_decode_breadboard` |
| cyclesim | `python -m cyclesim run hw/tests/cyclesim/cpld_regfile_dual_read.yaml` |
| Logic VM | `python -m pytest tests/ -q` |
| CE parity | `pytest tests/test_mem_decode_breadboard.py` |
| CW pack | `python tools/verify_control_store.py` |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | v0.1 — archived |
| 2026-06-10 | v0.2 — archived ([pre-v1.0](../archive/pre-v1.0/README.md)) |
| 2026-06-10 | **v1.0** — single breadboard: CPLD GPR ~40 MC + 138×2 + 10b CW |
