# P12 — summary report

**Date:** 2026-07-13  
**Build code:** **P12** (PE1 + FE2 discipline)  
**Tier:** Research (non-normative)  
**Model:** [model/p12_ipc_model.py](model/p12_ipc_model.py)

## Verdict: **Conditional Go**

P12 is **PE1’s IF|EX + Harvard-like ports** with FE2’s **no-idle EX**, **stretch-on-fail** sheet, and **serial FE2 fallback**. Optimistic P12 matches PE1 (ALU stream **IPC → 1.0**). Lab failure must update visible SYS, not reintroduce Gi1 idle or wishful FE1.

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | P12 opt == PE1 IPC? | **Yes** — same costs; ALU stream IPC **1.000** @ 2 MHz. |
| 2 | Stretch impact? | MEM/BEQ(t)/CALL/RET **+1** SYS each; balanced IPC **0.364 → 0.320**. |
| 3 | Fallback cost? | `fallback_fe2` = FE2; ALU stream **0.333** vs P12 **1.000**. |
| 4 | BOM vs PE1? | **+0 DIP** ([bom-delta.md](bom-delta.md)). |
| 5 | Mailbox @ 2 MHz? | Same Conditional Go as PE1; stretch MEM if RP late. |

## Evidence snapshot (`F_SYS = 2 MHz`)

| Mix | Gi1 | FE2 | PE1 / P12 | P12 stretch | fallback |
|-----|----:|----:|----------:|------------:|---------:|
| ALU×20 stream IPC | 0.200 | 0.333 | **1.000** | **1.000** | 0.333 |
| ALU×20 cold IPC | 0.200 | 0.333 | 0.500 | 0.500 | 0.333 |
| balanced IPC | 0.216 | 0.308 | **0.364** | 0.320 | 0.308 |
| balanced M/s | 0.432 | 0.615 | **0.727** | 0.640 | 0.615 |

Run: `python model/p12_ipc_model.py`.

## Copy bandwidth (DataReady only)

| Mode | SYS/B | B/s @ 2 MHz |
|------|------:|------------:|
| Gi1 | 9 | ≈ 222 KB/s |
| FE2 / PE1 / **P12** | 7 | ≈ **286 KB/s** |
| P12 stretch | 9 | ≈ 222 KB/s |

## Conditions before any P12 normative proposal

1. All PE1 lab / fit / BOM gates still apply.
2. Stretch columns stay in the programmer sheet; no silent idle return.
3. Fallback to serial FE2 is a **named mode** if ports fail ([fallback-fe2.md](fallback-fe2.md)).
4. Stretch before raising f_SYS ([clock-candidates.md](clock-candidates.md)).
5. Keep Gi1 normative until PE1/P12 lab + fit pass.

## Contrast

| | FE2 | PE1 | **P12** |
|--|-----|-----|---------|
| Extra silicon | none | ~6–10 DIP | **same as PE1** |
| Steady ALU IPC | ~0.33 | ~1.0 | **~1.0** (opt) |
| Lab fail | stretch E | increase stall | **stretch sheet (FE2 policy)** |
| Ports fail | — | stuck / redesign | **fallback FE2** |

## Next steps

1. Prefer P12 over raw PE1 when documenting lab stretch / fallback.
2. Breadboard PE1 ports first; apply stretch policy from day one.
3. Do not edit normative multiphase tables yet.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial desk study — Conditional Go |
