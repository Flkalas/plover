# ATF1504 FSM fit study — research report

**Date:** 2026-07-06  
**Scope:** Research only — v1.0 production (`cpld_fsm/hdl/`, `reference/**`) **unchanged**  
**Sandbox:** `cpld_fsm/fit-study/`

---

## 1. Executive summary

v1.0 Tier C achieves **WinCUPL Design fits** at **32/32 user I/O** by exporting only **`q_a0..2` and `q_b0..2`** (6 of 16 GPR read bits). Full logical parity needs **42 package pins** — **10 pins over** the ATF1504 PLCC-44 cap.

Production uses **43 unique macrocells** (JED parse, MC0–MC63 range) with **21 MC indices spare** in the fuse map — within the study gate of ≤56 used, but **no headroom for full `q_a`/`q_b` export** without architectural change.

| Rank | Variant | Full I/O | MC relief | BOM | Verdict |
|------|---------|----------|-----------|-----|---------|
| **1** | **A1+A2+A3** | Yes (off-chip GPR) | High | +3×574, −2×574 CW | **Recommended** for single ATF1504 |
| **2** | **D5a+A1** | Yes | Highest (no LUT) | +EEPROM, +3×574 | **Recommended** if CW table burn acceptable |
| **3** | **C2 ATF1508** | Yes | High | CPLD swap | Desk-check PASS; tool/BOM cost |
| **4** | **C1 dual ATF1504** | Yes | Split | +1 CPLD | Lowest ISA risk, highest wiring |
| **5** | **D1 Flash `$4000`** | Partial | High | +0 | Avoid unless Nano burn pipeline reused |
| — | **Baseline Tier C** | No (q trim) | — | Current | **Keep v1.0** until adoption decision |

**Clock (unchanged datapath):** **2.0 MHz** nominal; **1.5 MHz** if A1 external 574 on breadboard ([timing-clock-table.md](timing-clock-table.md)).

**Go/no-go:** **No apply** in this study. Adopt **A1+A2+A3** or **D5a+A1** via separate v1.1 plan if breadboard full 8-bit GPR read is required.

---

## 2. Baseline (production Tier C)

| Metric | Value |
|--------|-------|
| Device | ATF1504AS-10JU44 |
| User I/O | 32/32 |
| Fitter | Design fits |
| Unique MCs (JED) | **43** / 64 rating |
| idx5 active rows | 20 / 128 |
| GPR export | `q_a0..2`, `q_b0..2` only |
| Strobes | Via **CW_LO/CW_HI** 574×2 |

Detail: [fit-logs/baseline-production.md](fit-logs/baseline-production.md)

---

## 3. Variant matrix

| ID | In | Out | Total | MC est. | Synthesis | ISA |
|----|---:|----:|------:|---------|-----------|-----|
| Baseline Tier C | 15 | 17 | 32 | 43 used | Fitted (prod) | v1.0 |
| A1+A2+A3 | 15 | 17 | 32 | ~15–25 after removal | Fork ready† | v1.0 minus HW TFR‡ |
| D5a+A1 | 7 | 6 | 13 | ≤40 target | Fork ready† | v1.0 FSM-only → CW ROM |
| ATF1508 | 15 | 27+ | ≤64 | ample | Desk only | v1.0 |
| Dual 1504 | split | split | 2×32 | split | Desk only | v1.0 |
| D1 Flash CW | 15 | ~12 | ~27 | LUT out | Not forked | archive-like |
| C + full q internal | 15 | 27 | 42 | — | **FAIL** | — |

† WinCUPL not executed in study environment — structural pin/MC analysis PASS.  
‡ TFR via external 157 mux (six opcodes) or software sequence.

Full pin tables: [pin-budget-variants.md](pin-budget-variants.md)

---

## 4. Timing and clock

| Path | max (ns) | Limits |
|------|----------|--------|
| P0 CPLD GPR → INC | 168 | Baseline |
| P1 574 GPR → INC | 176 | A1 |
| P6b EEPROM CW latch | ~110 | D5 (fetch slot) |

**Recommendation:** Derive OSC from [timing-clock-table.md](timing-clock-table.md) after adoption; no change required for research conclusion.

---

## 5. EEPROM CW (D5)

- Model: [sim/eeprom_cw.py](sim/eeprom_cw.py)
- Image: [fit-logs/eeprom_cw_image.hex](fit-logs/eeprom_cw_image.hex) (256 B)
- **pytest:** CW LO/HI bytes match production `fsm_golden` pack for all 20 active idx5 rows
- **Trade-off:** Separate burn step; `pc_load_en` vs `FLG_Z` may need CPLD merge outside EEPROM

Sub-variants: D5a (parallel EEPROM), D5b (SST39 `$4000`), D5c (serial — macro stretch).

---

## 6. Recommendation

### Primary: **A1+A2+A3** on single ATF1504

- Move **R0/R1/R2** to **574×3**; CPLD drives **`reg_we` + `w_sel` + 14 strobes** (32 pins).
- Remove Tier C **`cw_data[7:0]`** and CPLD GPR/TFR mux — largest MC win with **12-DIP ALU unchanged**.
- Add **157** (or equivalent) for TFR read mux off-CPLD.

### Secondary: **D5a+A1**

- Same GPR split; replace idx5 LUT with **EEPROM** on data bus + **`cw_oe`/`cw_le`/`cw_bank`** (13 CPLD pins).
- Best MC headroom; adds **AT28C64-class** IC and image generation ([scripts/gen_eeprom_cw.py](scripts/gen_eeprom_cw.py)).

### Not recommended now

- **Status quo q-trim** for normative 8-bit ALU operands.
- **D1** unless team explicitly wants Flash CW revival.
- **D5c serial** for 2 MHz macro budget.

---

## 7. Migration outline (future apply — out of scope)

If v1.1 adopts A1+A2+A3:

1. `plover-whitepaper.md` §6 block diagram  
2. `reference/hardware/system-architecture.md` — GPR off-CPLD  
3. `cpld-system-controller.md` §2 port list  
4. Archive or supersede Tier C in `control-word-latch.md`  
5. `BOM.md` 574 count (+3 GPR, −2 CW optional)  
6. Merge `fit-study/variants/a1_a2_a3/` → `cpld_fsm/hdl/` after WinCUPL sign-off  
7. M2b bring-up rewrite (external GPR)

---

## 8. Open items

| Item | Status |
|------|--------|
| WinCUPL F9 on variant forks | **Pending** — local machine |
| Used MC count from fitter log | JED baseline only (43 unique) |
| Breadboard wire length @ P2 | Not measured |
| ATF1508 WinCUPL device string | Not verified |
| TFR smoke with 157 mux | Not built |

---

## 9. Appendix A — artifacts

| Artifact | Path |
|----------|------|
| A1+A2+A3 PLD + LUT merge | `variants/a1_a2_a3/system_ctrl_gen.pld` |
| D5a PLD fork | `variants/d5a_eeprom/system_ctrl_gen.pld` |
| Synthesis notes | `fit-logs/*-synthesis.md` |
| Research tests | `tests/test_fit_study_models.py` |
| Scoring (plan §5) | A1+A2 **27**, D5a+A1 **26**, ATF1508 **27**, dual **25** |

---

## 10. Appendix B — bring-up

Not performed (research-only scope).
