# gi1_dp — CPLD-DP WinCUPL skeleton

**Parent:** [../../gi1-ac-mbr/README.md](../../gi1-ac-mbr/README.md)  
**Pin map:** [../../gi1-ac-mbr/pin-map.md](../../gi1-ac-mbr/pin-map.md)

Gi1 datapath: **R0 (AC) only**; `q_a[7:0]` → ALU A; **ALU B from `net_mbr`** (off-chip MBR 574).

| Δ vs rev G | Detail |
|------------|--------|
| GPR | **8 FF** (was 24) |
| G-IC | **`reg_we` only** |
| Outputs | **no `q_b`** |

**Not for production burn** until CU Gi1 idx5 + breadboard MBR→B wire verified.

## Files

| File | Role |
|------|------|
| [system_ctrl.pld](system_ctrl.pld) | DP equations |

## Local fit

```text
wincupl system_ctrl.pld system_ctrl.tt system_ctrl.jed
```

Desk expectation: **17/32 pins PASS**; MC **~10–18** (desk).
