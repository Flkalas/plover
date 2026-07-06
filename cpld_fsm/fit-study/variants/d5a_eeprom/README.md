# Variant D5a — EEPROM CW fetch sequencer (no idx5 LUT in CPLD)

External parallel EEPROM drives `D[7:0]`; CPLD exports `cw_oe`, `cw_le`, `cw_bank`, `reg_we`, `w_sel`.
Combined with A1 (GPR in 574×3).
