# Dual ATF1504 — partition survey (fit-study)

Split v1.0 functions across two PLCC-44 devices to preserve ISA with minimal per-chip pressure.

## Proposed partition

| Chip | Role | Est. outputs |
|------|------|-------------|
| **CPLD-A** | GPR 24 FF, `q_a`/`q_b`, `reg_we` | ~17 |
| **CPLD-B** | idx5 FSM, Tier C CW bus or direct strobes | ~10–17 |

**Inter-chip:** `OPC[4:0]`, `phase`, `d_in[7:0]`, `FLG_Z`, `CLK`, `reg_we`, `w_sel[1:0]` (bundle ~20 wires).

## Pin / MC

| Criterion | Assessment |
|-----------|------------|
| Per-chip I/O | Each block **≤32** — comfortable |
| Per-chip MC | LUT isolated from GPR FF — **likely ≤56 each** |
| BOM | +1 ATF1504 + 1 PLCC adapter |
| Wiring | Cross-board ribbon; breadboard congestion |

## Fit-study conclusion

No second JED burned in this study. **Desk check: PASS** for feasibility — lowest risk to v1.0 ISA, highest BOM/wiring cost.

## Recommendation rank

**3rd** — use when single 1504 variants fail WinCUPL or team rejects GPR externalization.
