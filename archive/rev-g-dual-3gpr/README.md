# rev G dual 3-GPR normative (superseded)

**Superseded:** 2026-07-07 by **v1.0 Gi1** (AC + MBR operand path)  
**Prior normative:** 3×GPR in CPLD-DP, TFR opcodes, G-IC 6-wire

## Why Gi1 replaced rev G

| Gate | rev G | Gi1 v1.0 |
|------|-------|----------|
| ph2 ADD @ 250 ns | PASS ~168 ns | PASS ~133 ns |
| CPLD-DP pins | 31/32 | 17/32 |
| ISA | R0,R1→R2 ADD + TFR | R0 ← R0+imm; no TFR |

## Restore prior normative prose

| Bundle | Path |
|--------|------|
| **Normative snapshot** | [rev-g-normative-snapshot/](rev-g-normative-snapshot/) (this tree) |
| **CPLD HDL** | [cpld-rev-g-hdl.tar.gz](cpld-rev-g-hdl.tar.gz) |
| **Fit study** | [fit-study-gpr-fsm.tar.gz](fit-study-gpr-fsm.tar.gz) |

## Current normative

[plover-whitepaper.md](../../plover-whitepaper.md) · [reference/hardware/system-architecture.md](../../reference/hardware/system-architecture.md) · [reference/hardware/cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md)

**Note:** Gi1 itself was later superseded by **v1.0 P12** (2026-07-13) — [gi1-v1.0-normative/](../gi1-v1.0-normative/).
