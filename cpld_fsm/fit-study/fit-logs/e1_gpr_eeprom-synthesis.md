# E1 GPR+EEPROM synthesis — desk-check

**Variant:** `e1_gpr_eeprom` (full `q` export)  
**Date:** 2026-07-06  
**WinCUPL:** Not run in study environment

## Structural analysis

| Block | Production MC | E1 change |
|-------|---------------|-----------|
| idx5 PLA LUT | ~15–25 | **removed** |
| Tier C CW pack/mux | ~6 | **removed** (`cw_data` bus) |
| GPR 24 FF | 24 | retained |
| TFR comb | ~8–12 | retained (E1b) |
| CW fetch seq | — | +~4 (from D5a) |
| `pc_load` merge | ~2 | retained (stub `lat_*`) |

**MC estimate:** 43 − 20 (LUT) − 6 (CW pack) + 4 (fetch) ≈ **21–33** unique MC → **≤56 gate PASS** (desk).

## Pin declaration (full fork)

| In | 15 |
| Out | 19 (`q`×16 + CW×3) |
| **Σ** | **34** (+2 vs 32 cap) |

Trim fork (`e1_gpr_eeprom_trim`): **24** I/O — PASS 32/32.  
Q14 fork (`e1_gpr_eeprom_q14`): **32** I/O — PASS 32/32.

## Action

```powershell
.\scripts\build-variant.ps1 -Variant e1_gpr_eeprom
```

Local: confirm **Design fits** and refresh pin lock if adopting.

## Related

- [e1-pin-matrix.md](e1-pin-matrix.md)
- [e1-tfr-isa-mc.md](e1-tfr-isa-mc.md)
- [pin-budget-e1.md](../pin-budget-e1.md)
