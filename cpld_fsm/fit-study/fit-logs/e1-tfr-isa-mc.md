# E1 TFR ISA — MC desk-check

**Date:** 2026-07-06  
**Method:** Equation count from PLD snippets + production [`system_ctrl.pld`](../../hdl/system_ctrl.pld) L81–97

## Production TFR-v10 (baseline)

| Resource | Est. MC / terms |
|----------|----------------|
| `tfr_valid` | 6 product terms (6-opc OR) |
| `xfer_b[7:0]` | 8 × 3-input mux |
| `w_sel[1:0]` | 2 AND with `tfr_valid` |
| `gpr_d[7:0]` | 8 × 2:1 mux |
| **Total TFR comb** | **~8–12 MC** |

## Variant comparison

| ID | `tfr_valid` | Data path | Extra state | Phases/insn | 6/6 pairs |
|----|-------------|-----------|-------------|-------------|-----------|
| TFR-v10 | 6 OR | 3-mux src | — | 1 | yes |
| TFR-3bit | 1 AND | idx→src/dst LUT | — | 1 | yes |
| TFR-ring-2bit | 3 OR | fixed ring | — | 1 | **3 only** |
| TFR-ring-macro | 3 OR + seq | ring × hops | sub-phase | 2 (cold) | yes (clobber) |
| TFR-tmp-2op | 2-bit decode | TMP 4-mux | **+8 FF**, `tfr_sub` | 2 | yes (no clobber) |

## Trade-off notes

1. **TFR-3bit** — best comb simplification at **ISA break** cost; fits E1a (EEPROM CW per idx).
2. **TFR-ring-2bit** — lowest decode MC but **half coverage** without SW/macro.
3. **TFR-tmp-2op** — saves GPR clobber vs ring-macro; pays **+8 FF + 2× phase stretch** per TFR.
4. **E1b default** — keep **TFR-v10** for zero ISA change; LUT removal already yields MC headroom.

## PLD snippets

- [`tfr_3bit.pld`](../variants/e1_gpr_eeprom/tfr_3bit.pld)
- [`tfr_ring.pld`](../variants/e1_gpr_eeprom/tfr_ring.pld)
- [`tfr_tmp_2op.pld`](../variants/e1_gpr_eeprom/tfr_tmp_2op.pld)

WinCUPL fit not run — structural estimate only.
