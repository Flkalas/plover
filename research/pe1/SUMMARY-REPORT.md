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
| 6 | Elevated f_SYS / which OSC? | Margin **≥ 20–30%** of BEQ 227 ns or **≥ 50 ns** measured ([clock-candidates.md](clock-candidates.md)). **3.6864 MHz half-can** ≈ 44 ns (~19%) — preferred trial above 2 MHz; **4.0 MHz** ≈ 23 ns (~10%) — stress only. Lab: [beq-lab.md](beq-lab.md). |

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

**Note (2026-07-13):** PE1 machine + P12 discipline are now **Active v1.0 P12** in reference ([system-architecture.md](../../reference/hardware/system-architecture.md), [cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md)). Remaining gates are **lab / bitstream**, not prose nomination.

1. Accept BOM delta (PROG latch path + pipe IR) on breadboard real estate.
2. Lab: IF||EX overlap on ADD stream at **low SYS** first; stretch stalls if unstable.
3. Programmer sheet = pipe table (bubbles are ISA-visible timing) — see Active CU doc.
4. CU pipe/stall **Design fits** on ATF1504 when PLD exists.
5. Do **not** add branch prediction in v1 of PE1/P12.
6. Lab-measure RP mailbox GPIO response; keep **≤ 80 ns** desk or stretch MMIO EX.
7. For f_SYS > 2 MHz: prefer **3.6864 MHz** over 4.0; gate on **measured BEQ slack ≥ 50 ns**.

## Contrast

| | Shared FE1 | FE2 | PE1 | P12 |
|--|------------|-----|-----|-----|
| Extra silicon | none | none | **yes** | same as PE1 |
| Steady ALU IPC | wishful 1 | ~0.33–0.5 | **~1.0** | **~1.0** + stretch/fallback |
| Mechanism | same tick | serial F/E | **overlap IF/EX** | PE1 + FE2 rules |
| Mailbox @ 2 MHz | (Gi1 baseline) | OK | **OK if RP≤80 ns** | same |
| Elevated OSC | — | — | **3.6864 trial; 4.0 stress** | stretch first |

## Next steps

1. Prefer P12 over raw PE1 when documenting lab stretch / fallback — **fed Active [v1.0 P12](../../reference/hardware/system-architecture.md)** / [cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md).
2. Breadboard PE1 ports first; apply stretch policy from day one.
3. Pipe CU `.pld` Design fits — follow Active CU doc (bitstream still pending).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Desk study **fed Active v1.0 P12** reference + pipe CU |
| 2026-07-13 | Link P12 (PE1 + FE2 discipline) |
| 2026-07-13 | Clock margin policy; 3.6864 candidate; BEQ lab |
| 2026-07-13 | Mailbox @ 2 MHz Conditional Go; copy B/s table |
| 2026-07-13 | timing-budget.md — IF/EX ns slack |
| 2026-07-13 | Initial desk study — Conditional Go |
