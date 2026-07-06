# Control and decode (v1.0 rev G)

**Related:** [system-architecture.md](system-architecture.md) · [microcode-spec.md](microcode-spec.md) · [cpld-system-controller.md](cpld-system-controller.md) · [rom-architecture.md](rom-architecture.md)

This document is the **single normative reference** for who decodes what on the v1.0 breadboard CPU. Other normative docs link here instead of redefining decode roles.

**Superseded:** Tier C single-CPLD + CW 574×2 — [archive/tier-c-single-cpld/README.md](../../archive/tier-c-single-cpld/README.md).

---

## 1. Layered responsibilities

| Layer | Block | Input | Output / effect | On v1.0 SoC? |
|-------|-------|-------|-----------------|--------------|
| **Program store** | SST39 Flash | Address | Instruction bytes, boot, utilities | Yes |
| **Macro sequencer** | **CPLD-CU** idx5 FSM | `IR[4:0]`, `phase`, `FLG_Z` | Direct strobes + G-IC to DP | Yes |
| **GPR datapath** | **CPLD-DP** | `d_in`, G-IC | `q_a`/`q_b`, GPR writes | Yes |
| **ALU control** | FSM row constants on CU | CU outputs | `net_cin`, `net_bctrl0..3`, `net_lgc0..3`, `net_153_s0/s1` | Yes — **no `alu8_decode` DIP** |
| **ALU execute** | alu8 (12 DIP) | A, B, control nets | `net_y*`, `net_c_hi` | Yes |
| **Memory CE** | 74HC138×2 + glue | `A[15:0]`, MAP, mailbox | `/CE` to SRAM×2 + Flash | Yes (off CPLD) |
| **12-opcode comb decode** | `alu8_decode` | `alu_sel[3:0]` | Control nets | **M1 bench only** |

```text
  Flash ROM          CPLD-CU (idx5)              CPLD-DP (GPR)           74HC off-CPLD
  program bytes  IR ──► macro phases ──► strobes ──► alu8 / MEM / PC
  boot, vector       G-IC (6) ─────────► GPR, q_a/q_b ──► alu8 A/B
  $4000 unused       TFR comb + branch merge
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

### CPLD pair (rev G)

| Chip | Function |
|------|----------|
| **CPLD-CU** | idx5 FSM + LUT; comb TFR detect; branch `PC_LOAD_EN`; **14 direct strobes** to SoC |
| **CPLD-DP** | GPR 24 FF; full async `q_a`/`q_b`; TFR src mux from G-IC `src[1:0]` |

FSM index (CU internal only):

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

**Not in CPLD:** memory `/CE`, mailbox MAP, `FETCH` addr mux. See [memory-map.md](memory-map.md).

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
| **Machine** | `simulators/cyclesim/data/isa.py`, `fsm_table.py` | Executable golden |
| **CPLD** | `system_ctrl_cu.pld`, `system_ctrl_dp.pld`, `gen_ctrl_lut.py` | Bitstream source |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | **rev G** — dual CPLD; CW latch layer removed |
| 2026-07-04 | Initial anchor: FSM-only v1.0 |
