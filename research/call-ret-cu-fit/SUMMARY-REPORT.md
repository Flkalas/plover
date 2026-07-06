# CALL/RET CPLD-CU fit — summary report

**Date:** 2026-07-07  
**Tier:** Research (non-normative)  
**Normative contract:** [microcode-spec.md](../../reference/hardware/microcode-spec.md) §2.3

## Verdict: **Conditional Go**

Gi1 v1.0 CALL/RET is **architecturally compatible** with the existing dual-CPLD model. Desk MC/pin budget ([mc-pin-budget.md](mc-pin-budget.md)) projects CU total **~34–52 MC** and **0 additional I/O pins** — within ATF1504AS **64 MC / 32 I/O** part rating with margin.

**Conditions before breadboard CU reburn:**

1. WinCUPL **Design fits = Yes** on `variants/gi1_cu_callret/` ([fit-report.txt](variants/gi1_cu_callret/fit-report.txt)).
2. Lab confirms macro_end stack sequence completes at **2 MHz** (or M3b documents 2-cycle macro_end if needed).
3. M2a CALL/RET smoke ([M2a-cpld-decode.md](../../reference/hw-bringup/M2a-cpld-decode.md) §5) passes on reburned JED.

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | idx5 +2 rows MC/pin impact | **Negligible** — same BRANCH template; idx5 24/28 |
| 2 | macro_end stack assist | **Feasible** — reuse `MEM_RD`/`MEM_WR`; internal RP latch; no new addr pins |
| 3 | RET `PC_in` mux | **0 extra output pins** — internal mux |
| 4 | Timing vs 2 MHz execute half | **Likely OK**; flag if stack assist needs 2-cycle macro_end |

## Reference linkage

| Document | Item |
|----------|------|
| M3a §3 | CALL/RET CU fit gate |
| M2a §3 | 22-row frozen table + fit report |
| compiler-isa-audit | CALL/RET packed; burn gated here |
| software-roadmap S2 | M3a + this report |

## Next steps

1. Complete PLD fork under `variants/gi1_cu_callret/` (fork from archive `gi1_cu` when CU `.pld` lands).
2. Run WinCUPL; update `fit-report.txt` with fitter output.
3. On **Design fits**, generate `system_ctrl_cu.jed` and execute M2a/M3b bring-up.

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | Initial desk study — Conditional Go pending WinCUPL |
