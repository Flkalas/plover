# Baseline production fit — extracted metrics

**Source:** `cpld_fsm/hdl/system_ctrl.jed`, `fit_report.txt`, `system_ctrl.pin`  
**Date captured:** 2026-07-06 (committed production)  
**Device:** ATF1504AS-10JU44 (`f1504ispplcc44`)

## Fitter status

| Field | Value |
|-------|-------|
| Status | **Design fits** |
| User I/O | **32 / 32** |
| Tool | WinCUPL + FIT1504 |

## Macrocell usage (from JED fuse notes)

| Metric | Value |
|--------|-------|
| Highest MC index referenced | **63** |
| Unique MCs with product terms | **43** |
| Part rating | 64 MC |
| Headroom (unique) | **21** MC indices unused in fuse map |
| Study gate | Target **≤56** used for variants with margin — baseline **43** meets gate |

> WinCUPL fitter log “N of 64 macrocells used” was not in repo; JED parse is the baseline for this study.

## idx5 LUT

| Field | Value |
|-------|-------|
| Active rows | 20 / 128 slots |
| TFR | Comb `tfr_valid` outside LUT |
| Source | `simulators/cyclesim/data/fsm_table.py` → `ctrl_lut.inc` |

## Pin export (Tier C trim)

| Exported | Internal / via CW latch |
|----------|-------------------------|
| `reg_we`, `cw_data[7:0]`, `cw_le`, `cw_bank` | — |
| `q_a0..2`, `q_b0..2` | `q_a3..7`, `q_b3..7` |
| — | `mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, ALU ctrl → **574×2** |

## Internal FF budget (PLD structure)

| Block | Buried FF / state |
|-------|-------------------|
| GPR R0/R1/R2 | 24 (`r00..r27`) |
| Phase | `ph0`, `ph1`, prev, `cw_cnt0/1` |
| w_sel | internal |

Variant **A1+A2** removes GPR + CW sequencer from CPLD → estimated **25–35 MC** product-term relief (not re-fit on production PLD).
