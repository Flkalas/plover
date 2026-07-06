# E1 — CPLD GPR + EEPROM FSM (fit-study)

**Status:** Research fork — **not** v1.0 production bitstream.

## Architecture

| Block | E1 CPLD | EEPROM / external |
|-------|---------|-------------------|
| GPR R0–R2 | 24 FF, `q_a`/`q_b` read | — |
| TFR (E1b) | `tfr_valid`, `xfer_b`, `gpr_d` mux, `reg_we`/`w_sel` merge | — |
| Phase FSM | `ph0`/`ph1`, `macro_end` | — |
| CW fetch | `cw_le`, `cw_bank`, `cw_oe`, `cw_addr[6:0]` | Parallel ROM image |
| idx5 strobes | — | 20 rows × 2 B → 574×2 |
| idx5 PLA LUT | **removed** | — |

**Policy:** **E1b** — TFR stays CPLD comb (same as v1.0 [`system_ctrl.pld`](../../../hdl/system_ctrl.pld) L81–97). EEPROM holds **20** non-TFR rows only ([`sim/eeprom_cw.py`](../../sim/eeprom_cw.py)).

## PLD forks

| File | `q` export | Notes |
|------|------------|-------|
| `system_ctrl.pld` | full 16 | Main E1 fork |
| `tfr_3bit.pld` | — | TFR decode variant (desk-check equations) |
| `tfr_ring.pld` | — | 2-bit ring hot-path decode |
| `tfr_tmp_2op.pld` | — | 4-reg TMP 2-phase TFR |

Trim/q14 pin variants: sibling dirs [`e1_gpr_eeprom_trim`](../e1_gpr_eeprom_trim/), [`e1_gpr_eeprom_q14`](../e1_gpr_eeprom_q14/).

## Package ports (E1b-full)

**In (15):** `opc[4:0]`, `d_in[7:0]`, `flg_z`, `clk`

**Out (19):** `q_a[7:0]`, `q_b[7:0]`, `cw_le`, `cw_bank`, `cw_oe`

**Internal:** `reg_we`, `w_sel[1:0]` (GPR write merge; not exported in E1b)

## Build

```powershell
.\scripts\build-variant.ps1 -Variant e1_gpr_eeprom
```

WinCUPL optional — logs to [`fit-logs/e1_gpr_eeprom-synthesis.txt`](../../fit-logs/e1_gpr_eeprom-synthesis.txt).

## Pin budget

[pin-budget-e1.md](../../pin-budget-e1.md) · [fit-logs/e1-pin-matrix.md](../../fit-logs/e1-pin-matrix.md)

## Report

[E1 report](../../REPORT-e1-gpr-eeprom.md) (separate from baseline [REPORT.md](../../REPORT.md)).
