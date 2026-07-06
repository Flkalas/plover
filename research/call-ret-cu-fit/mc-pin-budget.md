# CALL/RET — MC and I/O pin budget (desk)

**Baseline CU:** ~24–30 MC, ~21/32 I/O ([cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md), [system-architecture.md](../../reference/hardware/system-architecture.md)).

Part rating: ATF1504AS **64 MC**, **32 I/O**. Bring-up gate remains **Design fits** — numbers below are **estimates only**.

## Delta summary

| Block | MC delta (desk) | Pin delta (desk) | Notes |
|-------|-----------------|------------------|-------|
| idx5 +2 rows (CALL/RET) | +0–2 | 0 | Same BRANCH template as JMP; idx5 24/28 |
| LUT `lut_pc_load` for 0x06/0x07 | +0–1 | 0 | Shares JMP strobes |
| Stack assist FSM | +4–8 | 0 | Sub-state @ macro_end; reuses MEM strobes |
| RP / addr internal latch | +2–4 | 0 | 16-bit RP + return_pc; no new `net_addr` pins |
| 16-bit push/pop sequencing | +2–4 | 0 | Byte-wide bus; 2× MEM_WR or MEM_RD |
| RET `PC_in` mux | +1–2 | **0** | Internal mux — goal met |
| Overflow / underflow compare | +1–2 | 0 | Constant compare vs `$F600`/`$FEEF` |
| Halt-on-fault glue | +0–1 | 0 | Freeze phase FSM / suppress fetch |
| **Total CU delta** | **~10–22 MC** | **0** | |
| **Projected CU total** | **~34–52 MC** | **~21/32** | Headroom vs 64 MC rating |

## Pin budget (unchanged target)

Gi1 CU already exports 14 SoC strobes + 1 `reg_we`. Stack assist must **not** add:

- New `net_addr` outputs (use latched RP inside CU + existing address glue timing).
- New PC bus pins (RET pop feeds internal `PC_in` mux).

Desk conclusion: **I/O pin headroom ~11 spare** should remain sufficient.

## Risk register

| Risk | Mitigation |
|------|------------|
| MC overflow on ATF1504 | WinCUPL fit in `variants/gi1_cu_callret/fit-report.txt` |
| macro_end > 1 execute half | Scope on 2 MHz; optional 2-cycle macro_end in M3b lab notes |
| RP cell race with program STA | `$0F00` unreachable via Gi1 `LDA`/`STA` abs8 — CU-only path |

## Verification

| Step | Owner |
|------|-------|
| Desk table (this file) | Done |
| PLD spike + fitter | `variants/gi1_cu_callret/` |
| Sign-off | [SUMMARY-REPORT.md](SUMMARY-REPORT.md) |
