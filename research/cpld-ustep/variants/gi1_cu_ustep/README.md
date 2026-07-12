# Variant: `gi1_cu_ustep` (research spike)

**Status:** Skeleton — WinCUPL body **pending** (fork Gi1 CU `.pld` when available).  
**Parent study:** [../README.md](../README.md)

## Intent

Spike CPLD-CU for dual-clock research:

1. Input **`CLK_USTEP`** (fast sequencer).
2. Input **`CLK_SYS`** (2 MHz — shared with DP / SoC edge).
3. Keep existing **14 SoC strobes + `reg_we`**; qualify all outputs in **SYS** domain.
4. Internal wait/ready FSM for bus ops.

## Desk pin / MC delta

| Item | Delta | Notes |
|------|------:|-------|
| `CLK_USTEP` input | **+1 I/O** | New net; DP stays on `CLK_SYS` only |
| Strobe sync FFs | **+4–10 MC** | 2-FF × several request groups (or shared sync + qualify) |
| Wait-state logic | **+2–6 MC** | Ready compare / busy |
| idx5 / LUT | ~0 | Same opcode table; finer internal step optional |
| **Projected CU** | baseline ~24–30 MC + **~6–16** | Still under 64 MC rating at desk |
| **I/O** | ~21 → **~22/32** | One spare used |

Bring-up gate remains WinCUPL **Design fits** — not these estimates.

## Files

| File | Role |
|------|------|
| [fit-report.txt](fit-report.txt) | Placeholder until fitter run |
| *(future)* `system_ctrl_cu.pld` | Fork from Gi1 CU |

## Out of scope (this spike)

- Changing CPLD-DP clocking
- Normative pin list in `reference/**`
- Breadboard reburn before [SUMMARY-REPORT.md](../SUMMARY-REPORT.md) promotes a path
