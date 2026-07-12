# Variant: `gi1_cu_ustep` (research spike)

**Status:** Skeleton — WinCUPL body **pending** (fork Gi1 CU `.pld` when available).  
**Parent study:** [../README.md](../README.md)

## Intent

Spike CPLD-CU for **related-clock** dual-CU research:

1. Input **`CLK_USTEP`** from the undivided (or ÷M) OSC net — same crystal as SYS.
2. Input **`CLK_SYS`** (2 MHz ÷N — shared with DP / SoC edge).
3. Keep existing **14 SoC strobes + `reg_we`**; qualify all outputs on **SYS-aligned** USTEP edges (sync enable), **not** an async 2-FF CDC block as the primary design.
4. Internal wait/ready FSM for bus ops; leave opcode-varying SYS costs for teaching e-IPC.

## Desk pin / MC delta

| Item | Delta | Notes |
|------|------:|-------|
| `CLK_USTEP` input | **+1 I/O** | Related OSC net; DP stays on `CLK_SYS` only |
| SYS-aligned qualify | **+4–10 MC** | Enable/mux on SYS slots (not async CDC baseline) |
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
- Async dual-osc CDC as the preferred spike path
