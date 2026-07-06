# Variant d5a_eeprom — synthesis log

| Field | Value |
|-------|-------|
| Variant | D5a + A1 (EEPROM CW on data bus, external GPR) |
| PLD fork | `variants/d5a_eeprom/system_ctrl.pld` |
| Device | `f1504ispplcc44` |
| WinCUPL | **Not run** in CI environment (desk check) |

## Pin budget (declared)

| Direction | Count |
|-----------|------:|
| Inputs | 7 (`OPC×5`, `FLG_Z`, `CLK`) |
| Outputs | 6 (`reg_we`, `w_sel×2`, `cw_oe`, `cw_le`, `cw_bank`) |
| **Total** | **13 / 32** |

## MC estimate

| Removed | Relief |
|---------|--------|
| Full `ctrl_lut.inc` idx5 PLA | **15–25 MC** |
| GPR FF bank | 25–30 MC |
| `cw_data[7:0]` pad drivers | 8 MC worth of IO cells |

**Target ≤40 MC** — **LIKELY PASS** (phase FSM + CW fetch only).

## EEPROM image

Generated: [eeprom_cw_image.hex](eeprom_cw_image.hex) (256 B, 128×2 byte idx5 table).  
Parity: `fit-study/tests/test_fit_study_models.py` vs production `fsm_golden` CW pack.

## Caveats

- `reg_we`/`w_sel` stubbed 0 in fork PLD — production D5 would encode in EEPROM or glue.
- `pc_load_en` dynamic (`FLG_Z`) may remain CPLD merge, not static EEPROM bit.

## Local action

F9 on `system_ctrl_gen.pld`; verify **Design fits** and MC count.
