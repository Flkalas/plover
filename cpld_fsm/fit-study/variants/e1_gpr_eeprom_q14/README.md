# E1 q14 — 32/32 with 7-bit ALU read

Exports **`q_a0..6` + `q_b0..6`** (14 pins) + CW fetch (3) = 17 out, 15 in → **32/32**.

`q_a7`/`q_b7` internal — strap or buffer for MSB during bring-up.

Build: `.\scripts\build-variant.ps1 -Variant e1_gpr_eeprom_q14`
