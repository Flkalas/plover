# E1 — CPLD GPR + EEPROM FSM (fit-study report)

**Date:** 2026-07-06  
**Scope:** Research only — v1.0 production **unchanged**  
**Sandbox:** `cpld_fsm/fit-study/`  
**Baseline report:** [REPORT.md](REPORT.md) (not modified)

---

## 1. Executive summary

**E1** keeps **GPR R0–R2 in the CPLD** and moves **idx5 control** to a **parallel EEPROM** (20 rows × 2 B), removing the on-chip idx5 PLA and Tier C `cw_data` bus. **TFR** stays on CPLD comb (**E1b**, same as v1.0).

| Metric | E1b-full | E1b-trim | E1b-q14 |
|--------|----------|----------|---------|
| I/O total | **34** | **24** | **32** |
| vs 32 cap | **+2 FAIL** | PASS | **PASS** |
| vs 36 JTAG | PASS | PASS | −4 |
| MC estimate | ~21–33 | ~21–33 | ~21–33 |
| Full 8b `q` | Yes | No (6 bits) | 7b/export |

**Verdict:** E1 wins **MC headroom** (LUT out) but **not pins** at full `q`. For single ATF1504:

1. **Keep v1.0 Tier C** if q-trim acceptable and no EEPROM.
2. **E1b + q14 or trim** if CPLD GPR + EEPROM burn OK.
3. **E1b-full + JTAG GPIO (+4)** if full 8b read required.
4. **A1+A2+A3** still best for full I/O without EEPROM ([REPORT.md](REPORT.md) rank 1).

**Go/no-go:** No apply to v1.0 in this study.

---

## 2. CPLD vs EEPROM CW

| Block | CPLD | EEPROM / external |
|-------|------|-------------------|
| GPR 24 FF | yes | — |
| TFR comb (E1b) | yes | — |
| phase FSM | yes | — |
| CW fetch `cw_le`/`cw_bank`/`cw_oe` | yes | — |
| idx5 strobes | — | 574×2 latch |
| idx5 PLA | **removed** | — |

EEPROM image: [fit-logs/eeprom_cw_image.hex](fit-logs/eeprom_cw_image.hex) (256 B, 20 active rows). Model parity: [sim/eeprom_cw.py](sim/eeprom_cw.py).

**E1a** (TFR rows in EEPROM): same pins; saves TFR comb MC at cost of 6 extra CW rows — not default.

---

## 3. TFR encoding exploration

Fit-study only — see [tfr-isa-variants.md](tfr-isa-variants.md).

### 3.1 TFR-v10 (E1b baseline)

6 opcode, 1-phase, bit-field `dst`/`src`. **Zero ISA change.** CPLD: 6-opc OR + xfer mux.

### 3.2 TFR-3bit

`0x10|idx[2:0]` — 6/6 in 1 phase. Simplest `tfr_valid` decode. Compiler remap required.

### 3.3 TFR-ring-2bit

2-bit ring hot 3 only. Lowest comb MC; cold 3 pairs need 2-insn with **GPR clobber**.

### 3.4 TFR-ring-macro

Hardware 2-hop through GPR — still clobbers middle register.

### 3.5 TFR-tmp-2op

**R0–R2 + hidden TMP.** Every transfer = 2 micro-ops (`TMP←src`; `dst←TMP`). **6/6, no clobber.** Cost: +8 FF, 2 phases per TFR, ISA break.

### 3.6 Recommendation

| Priority | TFR choice | When |
|----------|------------|------|
| 1 | **TFR-v10 (E1b)** | Adopt E1 without ISA change |
| 2 | **TFR-3bit** | EEPROM path + need simpler decode |
| 3 | **TFR-tmp-2op** | Ring-style encode + must avoid clobber |
| — | ring-2bit alone | Not sufficient (3/6 coverage) |

MC desk-check: [fit-logs/e1-tfr-isa-mc.md](fit-logs/e1-tfr-isa-mc.md)

---

## 4. Pin exploration

Full tables: [pin-budget-e1.md](pin-budget-e1.md) · PASS/FAIL: [fit-logs/e1-pin-matrix.md](fit-logs/e1-pin-matrix.md)

| Question | Answer |
|----------|--------|
| Full 8b `q` on strict 32 pins? | **No** |
| Best 32-pin E1? | **E1b-q14** (7b export + strap MSB) or **E1b-trim** |
| Full 8b on 1504? | **JTAG +4** or external GPR (A1+A2) |
| `reg_we` off-package? | **Yes** (E1b internal merge) |

PLD forks:

| Variant | Dir |
|---------|-----|
| `e1_gpr_eeprom` | [variants/e1_gpr_eeprom/](variants/e1_gpr_eeprom/) |
| `e1_gpr_eeprom_trim` | [variants/e1_gpr_eeprom_trim/](variants/e1_gpr_eeprom_trim/) |
| `e1_gpr_eeprom_q14` | [variants/e1_gpr_eeprom_q14/](variants/e1_gpr_eeprom_q14/) |

---

## 5. MC / synthesis

| Block | Δ vs production |
|-------|-----------------|
| idx5 LUT | **−15~25 MC** |
| Tier C CW pack | **−~6 MC** |
| CW fetch | **+~4 MC** |
| TFR comb (E1b) | 0 |
| GPR 24 FF | 0 |

**Estimate:** ~21–33 unique MC → ≤56 gate **PASS** (desk).

Detail: [fit-logs/e1_gpr_eeprom-synthesis.md](fit-logs/e1_gpr_eeprom-synthesis.md)

WinCUPL not run in CI — run `.\scripts\build-variant.ps1 -Variant e1_gpr_eeprom` locally.

---

## 6. Comparison to baseline study

| Variant | GPR | CW store | TFR | Pins (full q) | MC |
|---------|-----|----------|-----|---------------|-----|
| Tier C (v1.0) | CPLD trim | CPLD LUT + Tier C | CPLD comb | 32 (q trim) | 43 |
| A1+A2+A3 | 574×3 | CPLD LUT direct | 157 mux | 32 | ~25–35 |
| D5a+A1 | 574×3 | EEPROM | SW/mux | 13–25 | ≤40 |
| **E1b** | **CPLD** | **EEPROM** | **CPLD comb** | **34** | ~21–33 |

**E1 niche:** M2b “GPR in CPLD” + LUT MC relief without external GPR chips — pays EEPROM + pin pressure.

---

## 7. Recommendations and open items

### Adopt if

- Breadboard accepts **EEPROM burn** and **q trim or q14**.
- MC margin needed while keeping **on-chip GPR**.
- **TFR-v10** ISA frozen.

### Do not adopt E1 if

- **Full 8b `q` + strict 32 pins** required → **A1+A2+A3**.
- EEPROM / bus arbitration unacceptable → stay **Tier C**.

### Open items

- [ ] WinCUPL F9 on three E1 forks (local)
- [ ] Breadboard EEPROM CW fetch timing (P6 slot)
- [ ] `lat_pc_load`/`lat_pc_flg_z` feedback from CW latch in full SoC
- [ ] TFR-tmp-2op phase stretch vs macro-cycle budget

### Tests (fit-study)

```
14 passed  cpld_fsm/fit-study/tests/
187 passed cpld_fsm/hdl/tests/  (regression)
```

---

## Artifacts index

| Path | Role |
|------|------|
| [REPORT-e1-gpr-eeprom.md](REPORT-e1-gpr-eeprom.md) | This report |
| [pin-budget-e1.md](pin-budget-e1.md) | Pin subcases |
| [tfr-isa-variants.md](tfr-isa-variants.md) | TFR encodings |
| [sim/gpr_flash_fsm.py](sim/gpr_flash_fsm.py) | E1 integration model |
| [sim/tfr_isa_models.py](sim/tfr_isa_models.py) | TFR variant decoders |
