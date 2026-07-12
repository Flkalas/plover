# P12 + mailbox @ 2 MHz (desk)

**Non-normative.** Baseline: [../pe1/mailbox-2mhz.md](../pe1/mailbox-2mhz.md).

## Verdict carry-forward

PE1 mailbox **Conditional Go** @ 2 MHz if RP ≤ **80 ns** still applies to P12 (same latches/BOM).

## FE2 stretch piece

If mailbox EX is late even at low SYS → **stretch MEM/MMIO EX +1** (visible), update [opcode-pipe-table.md](opcode-pipe-table.md). Do not treat clock raise as the first fix.

Copy B/s: P12 opt ≈ PE1 ≈ FE2 (**~286 KB/s** @ 2 MHz, `LDIO`+`STA16`). Stretch MEM raises SYS/B and lowers B/s.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
