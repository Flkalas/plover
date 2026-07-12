# PE1 — summary report

**Date:** 2026-07-13  
**Build code:** **PE1**  
**Tier:** Research (non-normative)  
**Model:** [model/pe1_ipc_model.py](model/pe1_ipc_model.py)

## Verdict: **Conditional Go**

Pipelined IF|EX with a **Harvard-like program/data split** and **~6–10 extra DIP-class parts** can recover **FE1-class throughput** (steady ALU **IPC → 1.0**) without branch prediction.  

This does **not** overturn the shared-bus FE1 **No** in [primitive-one-clock](../primitive-one-clock/SUMMARY-REPORT.md): PE1 **changes the machine** (ports + pipe), it does not make one A-bus edge do everything.

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | ALU stream IPC ≈ 1 with PE1? | **Yes** (model `alu_stream`: imm in prior EX shadow) — **Conditional** on PROG/DATA isolation working on breadboard. |
| 2 | BOM delta? | **~6–10** DIP adds ([bom-delta.md](bom-delta.md)): pipe 574s, PROG buffers, mux/CE glue. No PLL; no dual-port SRAM in baseline. |
| 3 | Bubbles visible? | **Yes** — mem_stall, taken-branch bubble, operand IF bytes, CALL/RET stack_extra ([opcode-pipe-table.md](opcode-pipe-table.md)). |
| 4 | Timing slack @ 2 MHz? | See [timing-budget.md](timing-budget.md): IF **~335 ns** / EX ADD **~352 ns** @ 500 ns period; BEQ stress @ 250 ns only **~23 ns**. |
| 5 | Mailbox @ 2 MHz + PE1 latches? | **Conditional Go** — EX mailbox **170 ns**, slack **330 @ 500** / **80 @ 250** if RP ≤ **80 ns** ([mailbox-2mhz.md](mailbox-2mhz.md)). Not the limiter (BEQ is). **No** vFDD fast path needed for **timing**; only for **B/s > ~0.3 MB/s**. |

## Timing snapshot (desk)

| Path | path ns | Slack @ 500 ns | Slack @ 250 ns |
|------|--------:|---------------:|---------------:|
| IF (Flash→IR) | 165 | **335** | 85 |
| EX ADD | 148 | **352** | 102 |
| EX mailbox | **170** | **330** | **80** |
| EX BEQ + squash | 227 | **273** | **23** |
| EX MEM | 130 | 370 | 120 |

Primary PE1 budget = **full SYS period 500 ns** (IF∥EX). Half-cycle 250 ns is a stress check; BEQ is the tight one; mailbox is comfortable if RP meets the assumption.

## Copy bandwidth (DataReady only)

| Model | SYS/B (`LDIO`+`STA16`) | B/s @ 2 MHz |
|-------|----------------------:|------------:|
| Gi1 | 9 | ≈ **222 KB/s** |
| FE2 / PE1 | 7 | ≈ **286 KB/s** |

`python model/mailbox_copy_bps.py` — PE1 ≈ FE2 for mailbox copy (DATA-bound).

## Evidence snapshot (`F_SYS = 2 MHz`)

| Mix | Gi1 IPC | FE2 IPC | PE1 IPC | PE1 rate |
|-----|--------:|--------:|--------:|---------:|
| ALU×20 stream | 0.200 | 0.333 | **1.000** | **2.000 M/s** |
| ALU×20 cold operand | 0.200 | 0.333 | 0.500 | 1.000 M/s |
| balanced (taken BEQ) | ~0.22 | ~0.31 | ~0.35 | ~0.7 M/s |

Exact numbers: run `python pe1_ipc_model.py`.

## Conditions before any PE1 normative proposal

1. Accept BOM delta (PROG latch path + pipe IR) on breadboard real estate.
2. Lab: IF||EX overlap on ADD stream at **low SYS** first; stretch stalls if unstable.
3. Document programmer sheet = pipe table (bubbles are ISA-visible timing).
4. CU pipe/stall **Design fits** on ATF1504 if PLD forked later.
5. Do **not** add branch prediction in v1 of PE1.
6. Lab-measure RP mailbox GPIO response; keep **≤ 80 ns** desk or stretch MMIO EX / update budget.

## Contrast

| | Shared FE1 | FE2 | PE1 |
|--|------------|-----|-----|
| Extra silicon | none | none | **yes** |
| Steady ALU IPC | wishful 1 | ~0.33–0.5 | **~1.0** |
| Mechanism | same tick | serial F/E | **overlap IF/EX** |
| Mailbox @ 2 MHz | (Gi1 baseline) | OK | **OK if RP≤80 ns** |

## Next steps

1. Optional breadboard sketch: PROG 245 + IR 574 wiring note.
2. Scope mailbox `LDIO` D-valid vs 80 ns assumption ([mailbox-2mhz.md](mailbox-2mhz.md)).
3. Keep Gi1 normative until PE1 lab + fit gates pass.
4. Prefer PE1 over cpld-ustep when the goal is **programmer 1-work≈1-clock**, not multiphase pedagogy.
5. vFDD fast path only if **throughput** goal exceeds ~0.3 MB/s copy — not required for 2 MHz timing closure.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Mailbox @ 2 MHz Conditional Go; copy B/s table |
| 2026-07-13 | timing-budget.md — IF/EX ns slack |
| 2026-07-13 | Initial desk study — Conditional Go |
