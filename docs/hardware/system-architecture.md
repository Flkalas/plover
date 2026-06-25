# Plover v1.0 — System Architecture

**Version:** 1.0 (pre-release) · **Date:** 2026-06-24  
**Status:** Active normative specification (breadboard)

**Design rationale:** [research/design-rationale-v1.0.md](research/design-rationale-v1.0.md)  
**Superseded prototype:** [prototype-flash-cw](../archive/prototype-flash-cw/README.md)

**Winner:** `op_legacy` + `dec_cpld_seq` + `cpld_3fixed` + **`cw_fsm_only`** + **`idx5`** (+ TFR `0x10–0x15`)

---

## 1. Overview

| Item | Specification |
|------|---------------|
| **CPU** | 8-bit TTL datapath: custom ALU (74HC, 14 DIP) + **3×GPR in ATF1504** (R0→A, R1→B, R2=result) |
| **Control** | **FSM-only (idx5)** — `(opcode[4:0]<<2)\|phase` in CPLD; **no Flash CW**; **no `alu8_decode`** |
| **ISA** | Opcode **`[4:0]`**; core `0x01–0x0F` + **Extended `0x10–0x1F`** (TFR `0x10–0x15`); `0x0C` reserved |
| **System CPLD** | **ATF1504AS-10JU44** — GPR + idx5 sequencer (~38 MC) |
| **CE decode** | **74HC138×2** + **74HC08/32/04** glue → RAM/ROM `/CE` (unchanged) |
| **Flags / branch** | **574×1 FLG** (Z/C) + CPLD `PC_LOAD_EN` |
| **RAM** | **2× IS62C256AL** — 64 KB via **A15** bank |
| **ROM** | **1× SST39SF010A** — boot + utility (**no control store @ `$4000`**) |
| **I/O** | MMIO **Mailbox** @ `$FF00–$FFFB` — polling only, **no IRQ** |
| **Coprocessor** | **RP2350B** — GPU, HID, virtual FDD (separate board) |

### Metrics (vs superseded prototype)

| Metric | [prototype-flash-cw](../archive/prototype-flash-cw/README.md) | **v1.0** |
|--------|----------------------------------------------------------------|----------|
| DIP (control path) | 31 | **20** (−11) |
| Critical delay | 151 ns | **136 ns** (−15) |
| Flash CW rows | 23 per-phase | **0** (FSM-only) |
| CPLD MC | ~40 | **~38** |

---

## 2. Design philosophy

- **Deterministic:** no IRQ; operator-visible mode switches.
- **Passive map:** mailbox/MAP in **discrete gates**; CPLD holds GPR + sequencer only.
- **Thin decode:** ALU controls from CPLD FSM, not comb `alu8_decode` block.
- **ROM as law:** boot + program only; Flash **`$4000` unused** ([rom-architecture.md](rom-architecture.md)).
- **Flat memory:** 64 KiB linear map; **no MMU** ([classic-memory-model-comparison.md](classic-memory-model-comparison.md)).

---

## 3. Block diagram

```text
  IR OPC[4:0] ──► CPLD idx5 FSM ──┬──► cin/b_sel/lgc/y_mux
                                  ├──► REG_WE (internal w_sel)
                                  ├──► MEM_RD/WR, Y_OE
                                  └──► PC_LOAD_EN
  q_a/q_b (R0,R1) ──► alu8 ◄── MBR/PC (574)
  FLG (574×1) ──► CPLD

  A[15:0] ──► 08/32 mailbox·MAP ──► 74HC138×2 ──► /CE ──► SRAM×2 + SST39
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

CPLD `ATF1504AS-10JU44` + PLCC→DIP (#15); Flash `SST39SF010A-70-4C-PHE` PDIP 직결; SRAM `IS62C256` + SOP28 (#3a)×2; `SN74LVC8T245` + SOIC-24 (#3c)×3. 상세: [parts-on-hand.md](../project/parts-on-hand.md) · [BOM.md](../../BOM.md).

---

## 6. Document index

| Document | Content |
|----------|---------|
| [memory-map.md](memory-map.md) | Address map, 138×2 + gate decode |
| [cpld-system-controller.md](cpld-system-controller.md) | CPLD GPR+idx5 FSM (~38 MC) |
| [microcode-spec.md](microcode-spec.md) | FSM-only ISA, idx5 |
| [hw-bringup/README.md](../hw-bringup/README.md) | M1–M5 breadboard bring-up |
| [hw-bringup/breadboard-wiring.md](../hw-bringup/breadboard-wiring.md) | SoC wiring (no decode block) |
| [research/design-rationale-v1.0.md](research/design-rationale-v1.0.md) | Design decisions (research) |
| [cpu-4axis-arch-search-report.md](cpu-4axis-arch-search-report.md) | Exploration record (research) |

---

## 7. Verification

| Layer | Gate |
|-------|------|
| Breadboard | M1–M5 bring-up checklists ([hw-bringup/README.md](../hw-bringup/README.md)) |
| FSM table | `python tools/verify_control_store.py --v1.0` |
| Scope | CPLD `REG_WE`, `MEM_RD`, `PC_LOAD_EN` vs FLG |

---

## 8. Forward work (not normative)

| Track | Status |
|-------|--------|
| **H1** `op_class` + `cpld_3seq` | Optional — [hardware/research/](research/README.md) |
| **H2** `cw16_direct` + `idx8` | P1 bypass path — microcode-spec appendix A |
| **MMU v1.1** | **Not adopted** — [archive/pre-v1.1-mmu/](../archive/pre-v1.1-mmu/README.md) |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | **v1.0** — FSM-only idx5 normative; prototype-flash-cw archived |
| 2026-06-10 | Flash-CW prototype (see archive) |
