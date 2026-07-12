# P12 BOM delta (desk)

**Non-normative.**

FE2 discipline (stretch sheet, no-idle EX, fallback mode) adds **0 DIP**.

Silicon = **same as PE1** — see [../pe1/bom-delta.md](../pe1/bom-delta.md) (~6–10 DIP-class adds: pipe 574s, PROG buffers, mux/CE glue).

CU may need a **mode bit / pin** for pipe vs serial FE2 fallback; count that in a future PLD fork, not as extra TTL.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial — link PE1 |
