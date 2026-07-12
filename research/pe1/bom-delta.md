# PE1 BOM delta vs Gi1 (desk)

**Non-normative.** Gi1 baseline: [BOM.md](../../reference/project/BOM.md). Counts are **ordering estimates**, not a purchase order.

## Already present (reuse)

| # | Part | PE1 role |
|---|------|----------|
| 18 | SST39SF010A Flash | **PROG** port (insn) |
| 19 | SRAM ×2 | **DATA** port |
| 14 | ATF1504 ×2 | CU pipe FSM + DP |
| 11 | 74HC574 ×3 | PC / MBR / FLG — extend usage |

## Added / increased (desk)

| Item | MPN class | Qty Δ | Why |
|------|-----------|------:|-----|
| Pipe IR / next-PC latch | 74HC574 | **+1..2** | Hold opcode / PC+1 while EX runs |
| Operand byte latch (imm/abs) | 74HC574 | **+1** | Overlap-safe MBR-like holding |
| PROG address buffer / latch | 74HC574 or 245 | **+1** | Isolate Flash addr from DATA A-bus |
| PROG data buffer | 74HC245 | **+1** | Isolate Flash D from SRAM D |
| A-bus mux widen | 74HC157 | **+1..2** | PC vs data-addr vs stack RP select without fighting IF |
| CE / OE glue | 74HC08/32 | **+1** | PROG vs DATA OE exclusivity when stalling |
| Decoupling | 0.1 µF | **+6..10** | New DIP |

**Desk total added DIP-class parts: ~6–10** (plus caps). No second crystal / PLL.

## Explicitly not added

| Reject | Why |
|--------|-----|
| Dual-port SRAM | Cost/complexity; default PE1 uses **mem_stall** instead |
| Branch predictor / BTB | Out of scope |
| Extra Flash for 24-bit µcode (Isetta-style) | Native ISA; CU stays CPLD |
| 3× Flash µstore | Rejected peer path |

## Fit note

CU MC rises for stall/flush logic — still under 64 MC **rating** at desk; gate remains WinCUPL **Design fits** if a PLD fork appears later.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial delta |
