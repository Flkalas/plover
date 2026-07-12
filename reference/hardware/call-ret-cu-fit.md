# CALL/RET CU fit desk (v1.0 P12)

**Status:** Active supporting desk — CALL/RET stack assist on CPLD-CU  
**Not:** a second CU architecture. Active schedule = [cpld-pipe-cu.md](cpld-pipe-cu.md). Stack contract = [microcode-spec.md](microcode-spec.md) §2.3.  
**Related:** [cpld-system-controller.md](cpld-system-controller.md) · [M2a-cpld-decode.md](../hw-bringup/M2a-cpld-decode.md) · [M3a-control-store.md](../hw-bringup/M3a-control-store.md)

## Verdict: Conditional Go (lab / Design fits)

CALL/RET return-stack assist is **architecturally compatible** with the dual-CPLD model (R0 + MBR→B, G-IC `reg_we`). Desk budget projects **0 additional I/O pins** and CU MC within the ATF1504AS **64 MC / 32 I/O** part rating with margin.

**Bring-up gate remains WinCUPL Design fits** — MC numbers below are **estimates only**, not normative BOM gates.

### Conditions before CU reburn / lab PASS

1. Pipe CU (or interim CU) **Design fits = Yes** on ATF1504AS.
2. Lab confirms **STACK_EX** push/pop sequence completes at **2 MHz** (document +1 STACK_EX / stretch if needed — [cpld-pipe-cu.md](cpld-pipe-cu.md) P12 rules).
3. M2a CALL/RET smoke and M3b fetch/execute checks pass on the programmed JED.

## Desk MC / pin summary

Part rating: ATF1504AS **64 MC**, **32 I/O**. Baseline CU desk ~24–30 MC, ~21/32 I/O ([cpld-system-controller.md](cpld-system-controller.md)).

| Block | MC delta (desk) | Pin delta | Notes |
|-------|----------------:|----------:|-------|
| CALL/RET decode / load path | ~0–2 | 0 | Shares redirect strobes with JMP |
| Stack assist FSM (**STACK_EX**) | ~4–8 | 0 | Reuses `MEM_RD` / `MEM_WR` |
| RP / return_pc internal latch | ~2–4 | 0 | No new addr pins |
| 16-bit push/pop sequencing | ~2 | 0 | Byte bus; multi-cycle EX |
| RET `PC_in` mux | ~1 | **0** | Internal mux |
| Overflow / underflow compare | ~1 | 0 | vs `$F600` / `$FEEF` |
| **Projected CU total** | **~34±2 MC** | **~21/32** | Headroom vs 64 MC rating |

Stack assist must **not** add new `net_addr` outputs or new PC bus pins (RET pop feeds internal `PC_in`).

## Mechanism (normative intent)

| Item | Choice |
|------|--------|
| RP cell | `$0F00` / `$0F01` (16-bit LE) — CU-owned path |
| Stack body | `$F600`–`$FEEF` |
| Strobes | Existing `MEM_RD` / `MEM_WR` |
| CALL | Push return PC; `PC_LOAD_EN` ← abs16; **STACK_EX** + bubble as needed |
| RET | Pop → `PC_in` (not MBR); **STACK_EX** + bubble |
| Pipe state | [cpld-pipe-cu.md](cpld-pipe-cu.md) **STACK_EX** |

## Risk register

| Risk | Mitigation |
|------|------------|
| MC overflow on ATF1504 | Design fits on pipe CU PLD |
| STACK_EX longer than one SYS | Stretch / multi-cycle EX on sheet; re-lab at low clock first |
| RP race with program stores | Keep `$0F00` CU-only; not a normal LDA/STA target |

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Active reference freeze (P12 **STACK_EX** wording); from 2026-07-07 desk Conditional Go |
| 2026-07-07 | Initial desk study (Gi1-era idx5 framing) |
