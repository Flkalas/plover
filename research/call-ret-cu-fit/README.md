# CALL/RET CPLD-CU fit study

**Status:** Research (non-normative)  
**Normative behavior:** [microcode-spec.md](../../reference/hardware/microcode-spec.md) §2.3 · [M3a-control-store.md](../../reference/hw-bringup/M3a-control-store.md) §2  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md) — M2a/M3a sign-off before CU JED reburn

## Scope

Verify that Gi1 **CPLD-CU** (ATF1504AS, 64 MC part rating, 32 I/O) can absorb:

1. **+2 idx5 LUT rows** — `0x06` CALL (idx5 **24**), `0x07` RET (idx5 **28**); 20 → **22** active slots.
2. **Return-stack assist @ macro_end** — RP cell `$0F00`, stack `$F600–$FEEF`, 16-bit LE push/pop via implicit `MEM_RD`/`MEM_WR`.
3. **RET `PC_in` mux** — popped return address vs MBR abs16 (JMP/CALL).
4. **Overflow / underflow** — `RP > $FEEF` or `RP ≤ $F600` → execution stop (HALT-class).

Flash `$4000` control words are **not** in scope — FSM-only path only.

## Baseline (Gi1 v1.0 CU)

| Item | Source |
|------|--------|
| MC desk | [cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) §8 — CU **~24–30 MC** |
| I/O desk | [system-architecture.md](../../reference/hardware/system-architecture.md) — CU **~21/32** pins |
| Pin pattern | [archive/gpr4-regfile-research.tar.gz](../../archive/gpr4-regfile-research.tar.gz) `gi1-ac-mbr/io-pin-allocation.md` (restored) |
| PLD fork | `variants/gi1_cu_callret/` — CU idx5 LUT + stack assist (this tree) |

## Deliverables

| File | Role |
|------|------|
| [architecture.md](architecture.md) | CU block diagram — stack assist, PC mux, strobes |
| [mc-pin-budget.md](mc-pin-budget.md) | Delta MC / pin estimate |
| [variants/gi1_cu_callret/](variants/gi1_cu_callret/) | WinCUPL PLD spike + `fit-report.txt` |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Go / No-go / conditional |

## Out of scope

- Normative used-MC counts in `reference/**`
- Breadboard JED burn (M2a after research pass)
- CPLD-DP changes (R0-only unchanged)
