# ATF1508AS — chip upgrade survey (fit-study)

| Field | ATF1504 (v1.0) | ATF1508AS (candidate) |
|-------|----------------|----------------------|
| Macrocells | 64 | **128** |
| User I/O | 32 (PLCC-44) | **up to 64** (TQFP-100) |
| WinCUPL device | `f1504ispplcc44` | `f1508as*` (verify install) |
| Adapter | PLCC-44 → DIP #15 | TQFP-100 adapter (not on BOM) |

## Fit-study conclusion (without local fitter run)

| Criterion | Assessment |
|-----------|------------|
| Full 42-pin logical budget | **Fits in I/O** with margin on 64-pin class |
| MC headroom | **128 MC** — idx5 LUT + GPR + Tier C with room |
| Toolchain | Requires WinCUPL device pack + programmer compatibility check |
| BOM | CPLD swap + adapter; same family as #14 |

## PLD fork

No `system_ctrl.pld` fork synthesized in this study — **desk check only**. Production Tier C + full `q_a`/`q_b` export is feasible on ATF1508-class parts pending tool verification.

## Recommendation rank

**2nd** (after A1+A2 on single 1504) if single-chip solutions fail synthesis or need >8 MC margin with full GPR inside CPLD.
