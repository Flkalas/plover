# Plover v1.0 — System Architecture

**Version:** 1.0 (pre-release) · **Hardware rev:** G dual-CPLD · **Date:** 2026-07-06  
**Status:** Active normative specification (breadboard)

**v1.0:** FSM-only **idx5** control, 3×GPR in **CPLD-DP**, Extended TFR bit-field (§ [microcode-spec.md](microcode-spec.md) §2.2), Flash `$4000` unused.

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC, 12 DIP) + **3×GPR in CPLD-DP** (R0→A, R1→B, R2=result) |
| **Control** | **FSM-only (idx5)** in **CPLD-CU** — `(opcode[4:0]<<2)\|phase`; **direct strobes** (no CW latch); **no `alu8_decode`** |
| **ISA** | Opcode **`[4:0]`**; core `0x01–0x0F` + **Extended TFR** (`0x11`,`0x12`,`0x14`,`0x16`,`0x18`,`0x19`); `0x0C` reserved |
| **System CPLD** | **2× ATF1504AS-10JU44** — CPLD-CU (control) + CPLD-DP (datapath) |
| **CE decode** | **74HC138×2** + **74HC08/32/04** glue → RAM/ROM `/CE` |
| **Flags / branch** | **574×1 FLG** (Z/C) + CPLD-CU `PC_LOAD_EN` |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot + utility (**no control store @ `$4000`**) |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

### Metrics (rev G vs superseded Tier C single-CPLD)

| Metric | Tier C (archived) | **rev G** |
|--------|-------------------|-----------|
| ATF1504 count | 1 | **2** |
| 574 (control path) | 5 (incl. CW×2) | **3** (PC/MBR/FLG) |
| Full 8b `q_a`/`q_b` | No (trim) | **Yes** |
| Branch BEQ desk @ 2 MHz | internal | internal (~212 ns) |

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive map:** mailbox/MAP in **discrete gates**; CPLD pair holds GPR + sequencer.
- **Thin decode:** ALU controls from CPLD-CU FSM, not comb `alu8_decode` block.
- **ROM as law:** boot + program only; Flash **`$4000` unused** ([rom-architecture.md](rom-architecture.md)).
- **Flat memory:** 64 KiB linear map; **no MMU**.

---

## 3. Block diagram

```text
  IR OPC[4:0] ──► CPLD-CU idx5 FSM ──► MEM_RD/WR, Y_OE, FLG_WE, PC_LOAD_EN
  FLG_Z ─────────► branch merge          cin/bctrl/lgc/s0/s1 ──► alu8
                    │
                    └── G-IC (6) ──► CPLD-DP GPR + full q_a/q_b ──► alu8 A/B
  d_bus[7:0] ─────────────────────────► CPLD-DP (LDA/STA write)

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

## 5. Physical packages (v1.0 breadboard rev G)

2× CPLD `ATF1504AS-10JU44` + 2× PLCC→DIP (#15); Flash `SST39SF010A-70-4C-PHE` PDIP 직결; SRAM `IS62C256` + SOP28 (#3a)×2; `SN74LVC8T245` + SOIC-24 (#3c)×3. 상세: [parts-on-hand.md](../project/parts-on-hand.md) · [BOM.md](../project/BOM.md).

---

## 6. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](memory-map.md) | Address map, 138×2 + gate decode |
| [cpld-system-controller.md](cpld-system-controller.md) | Dual CPLD CU/DP ports |
| [cpld-dual-routing.md](cpld-dual-routing.md) | G-IC bundle, breadboard placement |
| [cpld-dual-jtag.md](cpld-dual-jtag.md) | JTAG daisy chain |
| [microcode-spec.md](microcode-spec.md) | FSM-only ISA, idx5 |
| [hw-bringup/README.md](../hw-bringup/README.md) | M1–M5 breadboard bring-up |

---

## 7. Verification

| Layer | Gate |
|-------|------|
| Breadboard | M1–M5 bring-up checklists ([hw-bringup/README.md](../hw-bringup/README.md)) |
| FSM table | M3a checklist — opcode×phase logical consistency |
| Scope | CPLD-CU `REG_WE`, `MEM_RD`, `PC_LOAD_EN` vs FLG |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | **rev G** — dual ATF1504; direct strobes; full `q`; Tier C archived |
| 2026-06-24 | **v1.0** — FSM-only idx5 normative; prototype-flash-cw archived |
