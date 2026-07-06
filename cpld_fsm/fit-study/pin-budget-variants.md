# Pin budget — fit study variants

**Baseline (production Tier C):** [../hdl/pin_budget.md](../hdl/pin_budget.md) — **not modified** by this study.

**Device:** ATF1504AS-10JU44 PLCC-44 · **32 user I/O** (+ JTAG 7/13/32/38, GCLK 43)

## Logical full parity (normative port list)

| Group | Signals | Pins |
|-------|---------|-----:|
| Inputs | `OPC[4:0]`, `d_in[7:0]`, `FLG_Z`, `CLK` | 15 |
| GPR + strobe | `q_a[7:0]`, `q_b[7:0]`, `REG_WE` | 17 |
| Tier C CW | `cw_data[7:0]`, `cw_le`, `cw_bank` | 10 |
| **Total** | | **42** |

**Gap:** 42 − 32 = **10 pins** on a single ATF1504 with internal GPR + Tier C CW bus.

## Variant summary

| ID | Strategy | In | Out | Total | vs 32 | MC est. | Notes |
|----|----------|---:|----:|------:|------|---------|-------|
| **Baseline** | Tier C + q trim | 15 | 17 | 32 | 0 | 43 MC used† | Production fit |
| **A** | Tier A (no CW bus) | 17 | 16 | 33 | +1 | lower LUT IO | No external CW latch path |
| **A1+A2** | GPR external + direct strobes | 15 | 17 | **32** | 0 | ~25–35 freed | `reg_we`+`w_sel`+14 strobes |
| **A1+TierC** | GPR external + CW bus | 15 | 13 | 28 | −4 | moderate | Room for full `q` if GPR off-chip |
| **B** | JTAG as GPIO (+4) | — | — | 36 max | +4 | — | Still short of 42 with internal GPR |
| **C1** | Dual ATF1504 | split | split | 2×32 | — | 2× fit | GPR chip + FSM chip |
| **C2** | ATF1508 TQFP-100 | 15 | 27+ | ≤64 | — | 128 MC | Toolchain/device string TBD |
| **D1** | SST39 `$4000` CW | 15 | ~12 | ~27 | −5 | LUT removed | Program/CW share Flash |
| **D5a+A1** | EEPROM CW + GPR external | 7–15 | 6–10 | **18–25** | spare | **≤40 target** | `cw_oe`/`cw_le`/`cw_bank` + `reg_we`/`w_sel` |
| **D5c** | Serial EEPROM | +2 I2C | — | — | — | — | Macro-cycle stretch |

† From `system_ctrl.jed` fuse notes: **43 unique macrocells** (MC0–MC63 range), max index **MC63**. Part rating 64 MC.

## A1+A2 direct strobe breakdown (target variant X)

| Direction | Signals | Count |
|-----------|---------|------:|
| In | `OPC[4:0]`, `d_in[7:0]`, `FLG_Z`, `CLK` | 15 |
| Out | `REG_WE`, `w_sel[1:0]` | 3 |
| Out | `mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1` | 14 |
| **Total** | | **32** |

Off-CPLD: R0/R1/R2 in **574×3**; `bctrl1←bctrl0`, `bctrl3←bctrl2` at 153; TFR via **157** read mux (A3).

## D5a EEPROM CW breakdown (+ A1)

| Direction | Signals | Count |
|-----------|---------|------:|
| In | `OPC[4:0]`, `FLG_Z`, `CLK` (no `d_in` on CPLD) | 7 |
| Out | `REG_WE`, `w_sel[1:0]` | 3 |
| Out | `cw_oe`, `cw_le`, `cw_bank` | 3 |
| **Total** | | **13** |

EEPROM `D[7:0]` → shared data bus; CW bytes per [control-word-latch.md](../../reference/hardware/control-word-latch.md) §4.

## Tier reference (production)

| Tier | In | Out | Total | Status |
|------|---:|----:|------:|--------|
| A | 17 | 16 | 32 | Fits — no CW bus |
| **C (v1.0)** | 15 | 17 | 32 | Fits — CW bus + q trim |
| C + full `q_a`/`q_b` | 15 | 27 | 42 | **Does not fit** |
