# E1 pin matrix — PASS/FAIL

Desk-check from [pin-budget-e1.md](../pin-budget-e1.md). WinCUPL pad lock not run in CI.

| ID | Σ I/O | vs 32 cap | vs 36 JTAG | PASS 32? | PASS 36? | Recommendation |
|----|------:|----------:|-----------:|:--------:|:--------:|----------------|
| E1b-full | 34 | +2 | 0 | **FAIL** | **PASS** | Use JTAG GPIO or q trim |
| E1b-trim | 24 | −8 | −12 | PASS | PASS | **32/32 target**; loses full 8b ALU read |
| E1b-q14 | 32 | 0 | −4 | **PASS** | FAIL | Best single-1504 32-pin compromise |
| E1b-full-JTAG | 34 | +2 | 0 | FAIL | **PASS** | Tier B after ISP disconnect |
| E1a-full | 34 | +2 | 0 | FAIL | PASS | Same pins as E1b-full |
| E1-latch-in | 37 | +5 | +1 | FAIL | FAIL | Avoid |

## Answers (research gates)

| Question | Result |
|----------|--------|
| Full 8b `q` on strict 32 pins? | **No** — need JTAG +4, q14, or external GPR (A1+A2) |
| E1 better than Tier C on pins? | **No** at full `q`; **yes** on spare pins when `q` trimmed |
| `reg_we` off-package OK? | **Yes** (E1b) — internal merge + external latch for macro writes |
| q14 viable for breadboard? | **Desk PASS** — strap bit7 or buffer externally |

## Fork mapping

| Fork | Matrix row |
|------|------------|
| `e1_gpr_eeprom` | E1b-full |
| `e1_gpr_eeprom_trim` | E1b-trim |
| `e1_gpr_eeprom_q14` | E1b-q14 |
