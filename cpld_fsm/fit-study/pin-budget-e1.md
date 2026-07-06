# Pin budget — E1 (GPR in CPLD + EEPROM FSM)

**Baseline:** [pin-budget-variants.md](pin-budget-variants.md) · production [../hdl/pin_budget.md](../hdl/pin_budget.md) **unchanged**.

**Device:** ATF1504AS-10JU44 · **32 user I/O** (+ JTAG +4 → **36** run-mode GPIO)

## E1 architecture

| Block | Location |
|-------|----------|
| GPR R0–R2 (24 FF) | CPLD |
| TFR comb (`tfr_valid`, `xfer_b`, `reg_we`/`w_sel` merge) | CPLD (E1b) |
| phase FSM, `macro_end` | CPLD |
| CW fetch (`cw_le`, `cw_bank`, `cw_oe`, addr glue) | CPLD |
| idx5 strobes (`mem_rd`, ALU ctrl, non-TFR `reg_we`) | EEPROM → 574×2 latch |
| `ctrl_lut.inc` idx5 PLA | **removed** |

**vs Tier C:** `cw_data[7:0]` + `reg_we` pad (9 pins) → `cw_le`/`cw_bank`/`cw_oe` (3 pins); full `q_a`/`q_b` (+10 vs trim) → net **+1~2** over 32 cap.

## Input baseline (all E1 subcases)

| Signal | Count |
|--------|------:|
| `OPC[4:0]` | 5 |
| `d_in[7:0]` | 8 |
| `FLG_Z` | 1 |
| `CLK` | 1 |
| **In** | **15** |

## Subcase matrix

| ID | `q` export | CW pads | `reg_we` pad | Extra in | Out | **Σ** | vs 32 | vs 36 JTAG | Notes |
|----|------------|---------|--------------|----------|----:|------:|------:|------------|-------|
| **E1b-full** | 16 (`q_a`/`q_b` full) | 3 | 0 (internal merge) | — | 19 | **34** | **+2** | 34/36 OK | Target fork `e1_gpr_eeprom` |
| **E1b-trim** | 6 (Tier C same) | 3 | 0 | — | 9 | **24** | −8 | −12 | `e1_gpr_eeprom_trim` |
| **E1b-q14** | 14 (`q_a0..6`, `q_b0..6`) | 3 | 0 | — | 17 | **32** | **0** | −4 | `e1_gpr_eeprom_q14` desk-check |
| **E1b-full-JTAG** | 16 | 3 | 0 | — | 19 | **34** | +2 | **PASS** | Tier B +4 pads |
| **E1a-full** | 16 | 3 | 0 | — | 19 | 34 | +2 | — | TFR strobes in EEPROM rows |
| **E1-latch-in** | 16 | 3 | 0 | +3 (`reg_we_lat`, `w_sel`) | 19 | **37**† | +5 | +1 | CW Q feedback to CPLD (non‑권장) |

† In = 18 if latch feedback exported as inputs.

## Signal-level export (E1b-full)

| Direction | Signals | Count |
|-----------|---------|------:|
| In | `OPC[4:0]`, `d_in[7:0]`, `FLG_Z`, `CLK` | 15 |
| Out | `q_a[7:0]`, `q_b[7:0]` | 16 |
| Out | `cw_le`, `cw_bank`, `cw_oe` | 3 |
| Buried / internal | `reg_we`, `w_sel[1:0]` merge; EEPROM addr `cw_addr[6:0]` glue | — |

**Not on CPLD package (E1):** `cw_data[7:0]` (EEPROM drives bus); Tier C strobes via external latch.

## Research conclusions (desk-check)

1. **Strict 32/32 + full 8b `q`:** FAIL on single ATF1504 — use **q14**, **q trim**, **JTAG +4**, or **ATF1508** / **A1+A2**.
2. **E1 vs Tier C:** MC headroom from LUT removal; pin trade is **worse** unless `q` stays trimmed.
3. **`reg_we` off-package:** Valid for E1b — GPR CE from internal `tfr_valid` OR latched CW (breadboard wires latch Q to buried node in full SoC).

## Variant forks

| Fork dir | `q` bits | Purpose |
|----------|----------|---------|
| [variants/e1_gpr_eeprom/](variants/e1_gpr_eeprom/) | 16 | Logic + MC estimate |
| [variants/e1_gpr_eeprom_trim/](variants/e1_gpr_eeprom_trim/) | 6 | 32/32 pad lock attempt |
| [variants/e1_gpr_eeprom_q14/](variants/e1_gpr_eeprom_q14/) | 14 | 32/32 with 7b ALU read |

PASS/FAIL summary: [fit-logs/e1-pin-matrix.md](fit-logs/e1-pin-matrix.md)
