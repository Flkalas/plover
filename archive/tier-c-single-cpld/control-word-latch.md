# Control word latch (Tier C) v1.0

**Role:** Off-chip **74HC574×2** hold register for bus strobes and ALU controls that exceed ATF1504 PLCC-44 user I/O budget.

**Related:** [cpld-system-controller.md](cpld-system-controller.md) · [control-and-decode.md](control-and-decode.md) · [alu-opcodes-timing.md](alu-opcodes-timing.md) · [breadboard-wiring.md](../hw-bringup/breadboard-wiring.md)

---

## 1. Purpose

| Tier | CPLD package role | Limit |
|------|-------------------|-------|
| **A** | `q_a`/`q_b`, `REG_WE` only; other FSM outputs internal | 32/32 I/O; no `FLG_Z` / full strobes on pads |
| **B** | Reuse JTAG pads (7/13/32/38) as GPIO after ISP | +4 pads; still short for full sim parity |
| **C (normative SoC)** | CPLD drives **8-bit CW bus** + latch; **574×2** fan out to ALU and bus glue | Frees ~14 dedicated output nets |

v1.0 does **not** fetch per-phase control words from Flash ([M3a-control-store.md](../hw-bringup/M3a-control-store.md)). Tier C words are **computed inside the CPLD idx5 FSM** and **loaded into external latches at each phase boundary**. This is **not** the archived Flash `$4000` CW path ([rom-architecture.md](rom-architecture.md) mentions historical `CW_L`/`CW_H` only as archive context).

---

## 2. Block diagram

```text
                    ATF1504 CPLD
  IR OPC[4:0] ──► idx5 FSM + LUT ──► cw_data[7:0] ──┬──► D  CW_LO 574  Q ──► mem_rd, mem_wr, y_oe,
  FLG_Z ─────────► pc_load_en merge              ├──► D  CW_HI 574  Q ──► flg_we, pc_load_en,
  d_in[7:0] ─────► GPR FF                        │         │              cin, bctrl*, lgc*, s0/s1
                    q_a/q_b ─────────────────────┼─────────┘              (see §4)
                    REG_WE (direct)              │
                    cw_le, cw_bank ──────────────┘
```

**Fanout at 153 (normative):** `bctrl1` ← `bctrl0`, `bctrl3` ← `bctrl2` (same as CPLD internal fanout in `system_ctrl.pld`). Only `bctrl0` and `bctrl2` are stored in CW_LO.

---

## 3. CPLD interface

### Outputs (direct on CPLD)

| Signal | Width | Role |
|--------|------:|------|
| `q_a[7:0]`, `q_b[7:0]` | 16 | Async GPR read → ALU A/B |
| `REG_WE` | 1 | GPR write strobe (internal `w_sel`) |
| `cw_data[7:0]` | 8 | Muxed CW load data |
| `cw_le` | 1 | Rising edge clocks **both** 574s (74HC574 clock) |
| `cw_bank` | 1 | 0 = load CW_LO; 1 = load CW_HI |

### Inputs (unchanged)

| Signal | Source |
|--------|--------|
| `OPC[4:0]` | IR[4:0] |
| `d_in[7:0]` | Data bus |
| `FLG_Z`, `FLG_C` | FLG 574 |
| `CLK` | System clock (2 MHz) |

### Via CW latch (not CPLD package pins)

`MEM_RD`, `MEM_WR`, `Y_OE`, `FLG_WE`, `PC_LOAD_EN`, `cin`, `bctrl0..3`, `lgc0..3`, `s0`, `s1` — see §4.

---

## 4. CW bit map (normative)

16 active bits across two bytes. Net names align with cyclesim `CtrlLookup` merged outputs.

### CW_LO (`cw_bank` = 0)

| Bit | Signal | cyclesim net |
|-----|--------|--------------|
| 0 | `mem_rd` | `net_mem_rd` |
| 1 | `mem_wr` | `net_mem_wr` |
| 2 | `y_oe` | `net_y_oe` |
| 3 | `flg_we` | `net_flg_we` |
| 4 | `pc_load_en` | `net_pc_load_en` |
| 5 | `cin` | `net_cin` |
| 6 | `bctrl0` | `net_bctrl0` |
| 7 | `bctrl2` | `net_bctrl2` |

### CW_HI (`cw_bank` = 1)

| Bit | Signal | cyclesim net |
|-----|--------|--------------|
| 0 | `lgc0` | `net_lgc0` |
| 1 | `lgc1` | `net_lgc1` |
| 2 | `lgc2` | `net_lgc2` |
| 3 | `lgc3` | `net_lgc3` |
| 4 | `s0` | `net_153_s0` |
| 5 | `s1` | `net_153_s1` |
| 6–7 | reserved | tie **0** |

**Off-latch wiring:** `net_bctrl1` ← `net_bctrl0`; `net_bctrl3` ← `net_bctrl2` at the 153 mux2 inputs.

---

## 5. Load timing

1. On **phase entry** (internal `ph0`/`ph1` transition or macro start), the FSM presents the row's control bundle on `cw_data`.
2. **Load CW_LO:** `cw_bank=0`; assert `cw_le` for one `CLK` rising edge.
3. **Load CW_HI:** `cw_bank=1`; assert `cw_le` for one `CLK` rising edge.
4. For the remainder of the phase, CW latch outputs **hold**; ALU and bus glue use latched values.
5. `REG_WE` and GPR async reads are **not** passed through the CW latch.

```text
  phase N entry          phase N body              phase N+1
  ────┬──────────        ────────────────        ────┬────
      │ cw_bank=0, le↑         hold CW_LO/HI              │
      │ cw_bank=1, le↑                                    │
      └───────────────────────────────────────────────────┘
```

---

## 6. `pc_load_en`

Branch commit is merged **inside the CPLD** before serialization:

```text
pc_load_en = macro_end & lut_pc_load & (!lut_pc_flg_z | FLG_Z)
```

The result is driven onto **CW_LO[4]** during the load sequence for that phase. No external glue is required between FLG 574 and `PC_LOAD_EN` beyond the CW latch output net.

---

## 7. I/O budget (Tier C)

| Group | Signals | Pins |
|-------|---------|-----:|
| Inputs | `OPC[4:0]`, `d_in[7:0]`, `FLG_Z`, `CLK` | 15 |
| GPR + strobe | `q_a[7:0]`, `q_b[7:0]`, `REG_WE` | 17 |
| CW interface | `cw_data[7:0]`, `cw_le`, `cw_bank` | 10 |
| **Total if all exported** | | **42** |

Normative SoC wiring **does not** put all 17 GPR/strobe bits on the package simultaneously with full CW bus under the 32-pin cap. Target fit strategy:

- Export **full `q_a`/`q_b` + `REG_WE` + CW bus (10)** with fitter-assigned pads, or
- Trade one `q` byte for `FLG_Z` on a dedicated input pad as needed.

See developer [pin_budget.md](../../cpld_fsm/hdl/pin_budget.md) for fitter Tier notes.

---

## 8. BOM delta

| IC | v1.0 before Tier C | Tier C |
|----|-------------------|--------|
| 74HC574 | 3 (PC, MBR, FLG) | **5** (+ **CW_LO**, **CW_HI**) |

[BOM.md](../project/BOM.md) item **#11**.

---

## 9. Bring-up smoke (M2a / M3a)

- [ ] Scope `cw_le` pulses at phase boundaries on ADD and LDA macros
- [ ] CW_LO[2] (`y_oe`) high during ADD ph0–ph2 ([cpld-system-controller.md](cpld-system-controller.md) §7)
- [ ] CW_LO[0] (`mem_rd`) high during LDA ph0 only
- [ ] CW_LO[4] (`pc_load_en`) pulses at BEQ macro_end when FLG_Z=1
- [ ] CW_HI ALU field matches ADD row in [alu-opcodes-timing.md](alu-opcodes-timing.md) during execute phases

---

## 10. Opcode spot-check (CW vs FSM table)

Normative cross-check against [cpld-system-controller.md](cpld-system-controller.md) §7.

| Macro | Phase | CW_LO bits set | CW_HI (ALU) |
|-------|-------|----------------|-------------|
| **ADD** `0x01` | ph0 | `y_oe` (bit 2) | ADD: `cin=0`, `bctrl=1100`, `lgc=0`, `s0=s1=0` |
| **ADD** | ph1 | `y_oe`, ( `REG_WE` direct, not CW) | ADD |
| **ADD** | ph2 | `y_oe`, `flg_we` (bit 3) | ADD |
| **LDA** `0x02` | ph0 | `mem_rd` (bit 0) | NOP |
| **LDA** | ph1 | — | NOP |
| **BEQ** `0x04` | ph0 | — | SUB |
| **BEQ** | ph1 | — | NOP |
| **BEQ** | macro_end | `pc_load_en` iff `FLG_Z` (bit 4) | — |

---

## Related documents

| Topic | Document |
|-------|----------|
| CPLD ports, phase tables | [cpld-system-controller.md](cpld-system-controller.md) |
| Decode layers | [control-and-decode.md](control-and-decode.md) |
| ALU opcode constants | [alu-opcodes-timing.md](alu-opcodes-timing.md) |
| SoC wiring | [breadboard-wiring.md](../hw-bringup/breadboard-wiring.md) |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | Initial Tier C normative spec — 8-bit mux CW bus, 574×2 |
