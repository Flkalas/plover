# Variant a1_a2_a3 — synthesis log

| Field | Value |
|-------|-------|
| Variant | A1+A2+A3 (external GPR, direct strobes, no TFR in CPLD) |
| PLD fork | `variants/a1_a2_a3/system_ctrl.pld` |
| Merged | `system_ctrl_gen.pld` (includes production `ctrl_lut.inc`) |
| Device | `f1504ispplcc44` |
| WinCUPL | **Not run** in CI environment (desk check) |

## Pin budget (declared)

| Direction | Count |
|-----------|------:|
| Inputs | 15 |
| Outputs | 17 (`reg_we`, `w_sel×2`, 14 strobes) |
| **Total** | **32 / 32** |

## MC estimate (vs baseline 43 unique)

| Removed from CPLD | Est. relief |
|-------------------|------------|
| GPR 24 FF + write decode | 25–30 MC |
| CW pack/mux/sequencer (8 `cw_data` + seq) | 4–8 MC |
| TFR `xfer_b*` mux | 8–12 MC |
| **Net** | **~35–45 MC product terms** → target **≤56** used |

## Structural fit assessment

| Gate | Result |
|------|--------|
| I/O ≤ 32 | **PASS** (declared) |
| idx5 LUT retained | **PASS** (same `ctrl_lut.inc`) |
| MC ≤ 56 | **LIKELY PASS** (pending local F9) |

## Local action

Open `system_ctrl_gen.pld` in WinCUPL → F9 → confirm **Design fits** → save fit log here.
