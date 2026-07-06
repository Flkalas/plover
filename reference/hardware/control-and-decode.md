# Control and decode (v1.0 Gi1)

**Related:** [system-architecture.md](system-architecture.md) · [microcode-spec.md](microcode-spec.md) · [cpld-system-controller.md](cpld-system-controller.md) · [rom-architecture.md](rom-architecture.md)

This document is the **single normative reference** for who decodes what on the v1.0 breadboard CPU.

**Superseded:** rev G 3-GPR + TFR — [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md). Tier C single-CPLD — [archive/tier-c-single-cpld/README.md](../../archive/tier-c-single-cpld/README.md).

---

## 1. Layered responsibilities

| Layer | Block | Input | Output / effect | On v1.0 SoC? |
|-------|-------|-------|-----------------|--------------|
| **Program store** | SST39 Flash | Address | Instruction bytes, boot, utilities | Yes |
| **Macro sequencer** | **CPLD-CU** idx5 FSM | `IR[4:0]`, `phase`, `FLG_Z` | Direct strobes + G-IC `reg_we` | Yes |
| **GPR datapath** | **CPLD-DP** | `d_in`, `reg_we` | `q_a` ← R0; write R0 | Yes |
| **Operand B** | **MBR 574** | Fetch | `net_mbr` → ALU B (off CPLD) | Yes |
| **ALU control** | FSM row constants on CU | CU outputs | `net_cin`, `net_bctrl0..3`, `net_lgc0..3`, `net_153_s0/s1` | Yes — **no `alu8_decode` DIP** |
| **ALU execute** | alu8 (12 DIP) | A, B, control nets | `net_y*`, `net_c_hi` | Yes |
| **Memory CE** | 74HC138×2 + glue | `A[15:0]`, MAP, mailbox | `/CE` to SRAM×2 + Flash | Yes (off CPLD) |
| **12-opcode comb decode** | `alu8_decode` | `alu_sel[3:0]` | Control nets | **M1 bench only** |

```text
  Flash ROM          CPLD-CU (idx5)              CPLD-DP (R0)            MBR 574
  program bytes  IR ──► macro phases ──► strobes ──► alu8 / MEM / PC
  boot, vector       reg_we ───────────► R0, q_a ──► alu8 A
  $4000 unused                              net_mbr ───────────────► alu8 B
  A[15:0] ─────────────────────────────────────────────────────► 138×2 ──► /CE
```

---

## 2. Flash vs CPLD

### Flash (SST39SF010)

| Region | Role |
|--------|------|
| `$0000+` | Program, bootloader, utility tables |
| `$FFFC` | Reset vector image |
| **`$4000–$4FFF`** | **Reserved — unburned in v1.0** |

### CPLD pair (Gi1)

| Chip | Function |
|------|----------|
| **CPLD-CU** | idx5 FSM + LUT; branch `PC_LOAD_EN`; **14 direct strobes** to SoC |
| **CPLD-DP** | **R0 (8 FF)**; async `q_a`; `reg_we` → R0 from `d_in` |

FSM index (CU internal only):

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

**Not in CPLD:** memory `/CE`, mailbox MAP, `FETCH` addr mux, **ALU B operand wire** (MBR). See [memory-map.md](memory-map.md).

---

## 3. ALU control signals (normative naming)

| Net | Role |
|-----|------|
| `net_cin` | 283 carry in (1 for SUB/CMP/**INC**) |
| `net_bctrl0..3` | 153 mux2 data pattern |
| `net_lgc0..3` | 153 mux1 logic pattern |
| `net_153_s0`, `net_153_s1` | Operand select → `y_mux_sel` |

**Fanout at 153:** `bctrl1` ← `bctrl0`, `bctrl3` ← `bctrl2` (CU ties internally).

**INC (opcode 9):** `cin=1`, `bctrl=0000` → A+0+1. See [b3-opcode.md](../hw-bringup/b3-opcode.md).

---

## 4. M1 bench vs SoC

| Context | Who drives ALU control? |
|---------|-------------------------|
| **M1 ALU bring-up** | Manual DIP / [b3-opcode.md](../hw-bringup/b3-opcode.md) |
| **M2+ integrated CPU** | **CPLD-CU** FSM outputs only |

---

## 5. Document index

| Topic | Document |
|-------|----------|
| ISA opcodes × phases | [microcode-spec.md](microcode-spec.md) |
| Dual CPLD ports, G-IC | [cpld-system-controller.md](cpld-system-controller.md) |
| Routing, JTAG, timing | [cpld-dual-routing.md](cpld-dual-routing.md), [cpld-dual-jtag.md](cpld-dual-jtag.md), [cpld-dual-timing.md](cpld-dual-timing.md) |
| Flash layout | [rom-architecture.md](rom-architecture.md) |
| ALU delay | [alu-opcodes-timing.md](alu-opcodes-timing.md) |

### Truth cascade (edit order)

| Tier | Path | Role |
|------|------|------|
| **Root** | [plover-whitepaper.md](../../plover-whitepaper.md) §6 | ISA / FSM narrative |
| **Reference** | `reference/**` | Normative detail |
| **Machine** | idx5 FSM golden tables | Executable parity (developer tree) |
| **CPLD** | Gi1 PLD forks | Bitstream source |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | **Gi1 v1.0** — AC + MBR; no TFR |
| 2026-07-06 | rev G archived |
| 2026-07-04 | Initial anchor: FSM-only v1.0 |
