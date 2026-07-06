# Plover v1.0 — System Architecture (Gi1)

**Version:** 1.0 · **Hardware:** Gi1 dual-CPLD · **Date:** 2026-07-07  
**Status:** Active normative specification (breadboard)

**v1.0 Gi1:** FSM-only **idx5** control, **R0 (AC) only** in CPLD-DP, **MBR→ALU B**, Flash `$4000` unused. Prior rev G 3-GPR archived.

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC, 12 DIP) + **R0 (AC) in CPLD-DP**; **MBR 574 → ALU B** |
| **Control** | **FSM-only (idx5)** in **CPLD-CU** — `(opcode[4:0]<<2)\|phase`; **direct strobes**; **no `alu8_decode`** |
| **ISA** | Opcode **`[4:0]`**; core `0x01–0x0F`; **`0x10–0x1F` reserved** (no TFR); `0x0C` reserved |
| **System CPLD** | **2× ATF1504AS-10JU44** — CPLD-CU + CPLD-DP (Gi1) |
| **CE decode** | **74HC138×2** + **74HC08/32/04** glue → RAM/ROM `/CE` |
| **Flags / branch** | **574×1 FLG** (Z/C) + CPLD-CU `PC_LOAD_EN` |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot + utility (**no control store @ `$4000`**) |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

### Metrics (Gi1 vs archived rev G)

| Metric | rev G (archived) | **Gi1 v1.0** |
|--------|------------------|--------------|
| CPLD-DP pins | 31/32 | **17/32** |
| CPLD-CU pins | 26/32 | **~21/32** |
| G-IC wires | 6 | **1** (`reg_we`) |
| ph2 ADD @ 2 MHz | ~168 ns PASS | **~133 ns PASS** |
| GPR in CPLD | R0–R2 (24 FF) | **R0 (8 FF)** |
| TFR opcodes | 6 | **none** |
| 574 count | 3 | **3** (unchanged) |

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive map:** mailbox/MAP in **discrete gates**; CPLD pair holds GPR + sequencer.
- **Thin decode:** ALU controls from CPLD-CU FSM, not comb `alu8_decode` block.
- **AC-centric:** single visible GPR; extra state in **RAM** (Gigatron-style).
- **ROM as law:** boot + program only; Flash **`$4000` unused** ([rom-architecture.md](rom-architecture.md)).
- **Flat memory:** 64 KiB linear map; **no MMU**.

---

## 3. Block diagram

```text
  IR OPC[4:0] ──► CPLD-CU idx5 FSM ──► MEM_RD/WR, Y_OE, FLG_WE, PC_LOAD_EN
  FLG_Z ─────────► branch merge          cin/bctrl/lgc/s0/s1 ──► alu8
                    │
                    └── reg_we ──► CPLD-DP R0 ──► q_a ──► alu8 A
  MBR 574 Q ──────────────────────────────────────────────► alu8 B
  d_bus[7:0] ─────────────────────────► CPLD-DP (write R0)

  A[15:0] ──► 08/32 mailbox·MAP ──► 74HC138×2 ──► /CE ──► SRAM×2 + SST39
```

Detail: [cpld-system-controller.md](cpld-system-controller.md) · [cpld-dual-routing.md](cpld-dual-routing.md)

---

## 4. Boot workflow

1. Power on — **MAP_MODE=Boot** (DIP default).
2. **RESET** — fetch @ **`$FFFC`** (**74HC157** addr MUX) → ROM vector → boot @ `$0000–$07FF`.
3. Bootloader: POST → vFDD load (Mailbox) → copy kernel to **RAM `$0800+`** → **`JMP $0800`** or halt.
4. Operator DIP → **Run**, **RESET** → fetch `$FFFC` from **RAM**.

Details: [bootloader.md](../boot/bootloader.md) · [memory-map.md](memory-map.md).

---

## 5. Physical packages (v1.0 breadboard Gi1)

2× CPLD `ATF1504AS-10JU44` + 2× PLCC→DIP (#15); Flash `SST39SF010A-70-4C-PHE` PDIP; SRAM `IS62C256` + SOP28 (#3a)×2; `SN74LVC8T245` + SOIC-24 (#3c)×3; **574×3** (PC/MBR/FLG). 상세: [parts-on-hand.md](../project/parts-on-hand.md) · [BOM.md](../project/BOM.md).

**Wiring delta vs rev G:** `net_mbr[7:0]` → `net_b[7:0]`; CPLD `q_b` disconnected.

---

## 6. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](memory-map.md) | Address map, 138×2 + gate decode |
| [cpld-system-controller.md](cpld-system-controller.md) | Dual CPLD Gi1 ports |
| [cpld-dual-routing.md](cpld-dual-routing.md) | G-IC, MBR→B wiring |
| [cpld-dual-jtag.md](cpld-dual-jtag.md) | JTAG daisy chain |
| [microcode-spec.md](microcode-spec.md) | FSM-only ISA, idx5 |
| [hw-bringup/README.md](../hw-bringup/README.md) | M1–M5 breadboard bring-up |

---

## 7. Verification

| Layer | Gate |
|-------|------|
| Breadboard | M1–M5 bring-up checklists ([hw-bringup/README.md](../hw-bringup/README.md)) |
| FSM table | M3a checklist — opcode×phase logical consistency |
| Scope | CPLD-CU `REG_WE`, `MEM_RD`, `PC_LOAD_EN` vs FLG; MBR hold on ADD |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | **Gi1 v1.0** — AC + MBR; rev G archived |
| 2026-07-06 | rev G dual ATF1504 |
| 2026-06-24 | v1.0 FSM-only idx5 normative |
