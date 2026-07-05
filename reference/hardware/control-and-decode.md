# Control and decode (v1.0)

**Related:** [system-architecture.md](system-architecture.md) · [microcode-spec.md](microcode-spec.md) · [cpld-system-controller.md](cpld-system-controller.md) · [rom-architecture.md](rom-architecture.md)

This document is the **single normative reference** for who decodes what on the v1.0 breadboard CPU. Other normative docs link here instead of redefining decode roles.

---

## 1. Layered responsibilities

| Layer | Block | Input | Output / effect | On v1.0 SoC? |
|-------|-------|-------|-----------------|--------------|
| **Program store** | SST39 Flash | Address | Instruction bytes, boot, utilities | Yes |
| **Macro sequencer** | ATF1504 CPLD idx5 FSM | `IR[4:0]`, `phase` | `REG_WE`, `MEM_RD/WR`, `Y_OE`, `PC_LOAD_EN`, internal `w_sel` | Yes |
| **ALU control** | Same CPLD FSM (per-row constants) | FSM row | `net_cin`, `net_bctrl0..3`, `net_lgc0..3`, `net_y_mux_sel`, `net_153_s0/s1` | Yes — **no `alu8_decode` DIP** |
| **ALU execute** | alu8 (12 DIP: 8×153 + 2×283 + 2×157) | A, B, control nets | `net_y*`, `net_c_hi` | Yes — **no opcode decode inside** |
| **Memory CE** | 74HC138×2 + 08/32/04 glue | `A[15:0]`, MAP, mailbox | `/CE` to SRAM×2 + Flash | Yes (off CPLD) |
| **12-opcode comb decode** | `alu8_decode` or M1 DIP cheatsheet | `alu_sel[3:0]` | Control nets | **M1 bench only** — not on SoC |

```text
  Flash ROM          CPLD (idx5 FSM)              74HC off-CPLD
  program bytes  IR ──► macro phases ──┬──► bctrl/cin/lgc/y_mux ──► alu8 (12 DIP)
  boot, vector       GPR R0→A, R1→B    ├──► MEM_RD/WR, Y_OE
  $4000 unused       CPLD FSM          └──► PC_LOAD_EN
  A[15:0] ─────────────────────────────────────► 138×2 ──► /CE
```

---

## 2. Flash vs CPLD

### Flash (SST39SF010)

| Region | Role |
|--------|------|
| `$0000+` | Program, bootloader, utility tables |
| `$FFFC` | Reset vector image |
| **`$4000–$4FFF`** | **Reserved — unburned in v1.0** (no per-phase control words) |

Flash holds **what to execute** (opcodes and immediates). It does **not** supply micro-phase strobes in normative v1.0.

### CPLD (ATF1504)

| Function | Role |
|----------|------|
| GPR 24 FF + fixed async read (R0→`q_a`, R1→`q_b`) | Sequenced macros |
| idx5 FSM + ALU ctrl outputs + branch + comb TFR | Per-phase strobes |
| **Fitter gate** | WinCUPL **Design fits** on ATF1504AS (64 MC device rating) |

FSM index (internal only):

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

Each active slot drives registered strobes for that macro phase. ALU settings for ADD/SUB/CMP/NOP are **constants in the FSM row**, not a separate 12-opcode combinational decoder.

**ADD vs CMP ph2:** ADD ph2 asserts REG_WE→R2; CMP ph2 is **flags_only** (FLG_WE, no REG_WE). Both require **mandatory REG_WE on ph1** (imm8→R1). See [cpld-system-controller.md](cpld-system-controller.md) §7.

**Not in CPLD:** memory `/CE`, mailbox MAP, `FETCH` addr mux (off-chip glue). See [memory-map.md](memory-map.md).

---

## 3. ALU control signals (normative naming)

SoC and ALU netlists use **Gigatron B_CTRL** names:

| Net | Role |
|-----|------|
| `net_cin` | 283 carry in (1 for SUB/CMP/**INC**) |
| `net_bctrl0..3` | 153 mux2 data pattern (2C0..2C3) |
| `net_lgc0..3` | 153 mux1 logic pattern (1C0..1C3) |
| `net_153_s0`, `net_153_s1` | Operand select → `y_mux_sel` |
| `net_y_mux_sel` | (= s0 \| s1) 157 picks sum vs logic |

**INC (opcode 9):** `cin=1`, `bctrl=0000` → A+0+1 (no glue, no `net_b0` repurposing). See [b3-opcode.md](../hw-bringup/b3-opcode.md).

Legacy **2-bit Flash CW B-mux select** encodings are **not** used on the v1.0 SoC datapath. Historical use is documented only under [prototype-flash-cw](../../archive/prototype-flash-cw/README.md).

---

## 4. M1 bench vs SoC

| Context | Who drives ALU control? |
|---------|-------------------------|
| **M1 ALU bring-up** (B3a) | Manual DIP / [b3-opcode.md](../hw-bringup/b3-opcode.md) cheatsheet, or optional `alu8_decode` block for CW-style tests |
| **M2+ integrated CPU** | CPLD FSM registered outputs only — **no `alu8_decode` on the breadboard** |

The `alu8_decode` netlist block remains in the repository for **isolated ALU verification**; it is not part of the v1.0 SoC BOM.

---

## 5. What is *not* a separate CPLD “ALU decode” block

A standalone **4-bit `alu_sel` → 12-opcode** combinational decoder (SOP ~70 gates or HC154 glue) would cost significant CPLD product-term budget if folded into the SoC FSM. v1.0 avoids this by:

1. FSM rows hard-code ALU controls for macro ops (ADD, SUB, CMP, NOP only).
2. Full 12-opcode truth table stays on **74HC ALU** (M1) or in simulation fixtures.

Do not conflate **“decode in CPLD”** (macro FSM) with **`alu8_decode` comb block**.

---

## 6. Document index

### Truth cascade (edit order)

| Tier | Path | Role |
|------|------|------|
| **Root** | [plover-whitepaper.md](../../plover-whitepaper.md) §6 | ISA / FSM narrative |
| **Reference** | [microcode-spec.md](microcode-spec.md), [M3a](../hw-bringup/M3a-control-store.md) §2 | Normative detail + frozen idx5 table |
| **Machine** | `simulators/cyclesim/data/isa.py`, `fsm_table.py` | Executable golden |
| **CPLD** | `gen_ctrl_lut.py` → `ctrl_lut.inc`; hand `system_ctrl.pld` (`tfr_valid`) | Bitstream source |

**Strobe layers:** LUT/csim tests use `reg_we_lut`, `w_sel*_lut` (18 signals). Bench/cyclesim merged pins use `reg_we`, `w_sel*`. Reference §7 tables describe merged behavior.

| Topic | Document |
|-------|----------|
| ISA opcodes × phases | [microcode-spec.md](microcode-spec.md) |
| CPLD ports, FSM templates | [cpld-system-controller.md](cpld-system-controller.md) |
| Flash layout | [rom-architecture.md](rom-architecture.md) |
| ALU opcode table + delay | [alu-opcodes-timing.md](alu-opcodes-timing.md) |
| M1 DIP cheatsheet | [b3-opcode.md](../hw-bringup/b3-opcode.md) |
| M3a FSM verify (no Flash CW) | [M3a-control-store.md](../hw-bringup/M3a-control-store.md) |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | Truth cascade (whitepaper root); strobe layer note |
| 2026-07-04 | Initial anchor: FSM-only v1.0, bctrl naming, INC=cin, M1 vs SoC decode split |
