# P12 BEQ lab (desk)

**Non-normative.** Procedure: [../pe1/beq-lab.md](../pe1/beq-lab.md).

## P12 emphasis

If BEQ + squash fails setup even at low SYS:

1. Prefer **+1 branch_bubble / EX stretch** (document in pipe table).
2. Re-measure.
3. Then raise f_SYS per [clock-candidates.md](clock-candidates.md).

Do not keep a broken single-bubble pack and “fix it with 4 MHz.”

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
