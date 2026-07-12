# P12 timing budget (desk)

**Non-normative.** Path ns / slack = PE1 — [../pe1/timing-budget.md](../pe1/timing-budget.md).

## P12 delta

| Item | Effect |
|------|--------|
| Optimistic pipe | Same IF∥EX budgets as PE1 @ 500 ns SYS |
| **Stretch** | Adds **SYS counts**, does not shorten the period |
| Raising f_SYS | Only after stretch + lab margin (see [clock-candidates.md](clock-candidates.md)) |

Primary limiter remains **BEQ** (PE1 stress ~23 ns @ 250 ns half-cycle). Stretch BEQ (+1) before chasing 4 MHz.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial — link PE1 |
