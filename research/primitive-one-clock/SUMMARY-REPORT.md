# Primitive one-clock — summary report

**Date:** 2026-07-13  
**Tier:** Research (non-normative)  
**Model:** [model/cycle_model.py](model/cycle_model.py) · [bus-timing-feasibility.md](bus-timing-feasibility.md)

## Verdicts

| Target | Verdict | One line |
|--------|---------|----------|
| **FE1** (fetch+execute = 1 SYS, full ISA) | **No** | Shared 8-bit von Neumann bus cannot fetch and do data/stack/multi-byte work in one tick; slowing SYS does not add a second port. |
| **FE2** (F then E, no idle phases) | **Conditional Go** | Drops ADD/CMP idle; programmer-visible multi-F / multi-E for abs16 and CALL/RET; needs CU rewrite + lab, not a normative claim yet. |

Owner intent (“1 work ≈ 1 clock, full timing control”) is **not met by FE1 on this BOM**. Closest honest regression is **FE2**: every counted SYS does bus/ALU/PC work; no blank CU padding.

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | FE1 on current breadboard @ 2 MHz? | **No** for core ISA. ALU-only path fits 250 ns, but FE1 fails on **address mux exclusivity** and multi-byte fetch. |
| 2 | FE2 as primitive regression? | **Conditional Go** — remove Gi1 idle; fixed F/E; document CALL/RET E×k. |
| 3 | Hard blockers? | Shared A-bus; 2–3 byte insns; stack mem; no Harvard in BOM. |

## Evidence snapshot (fetch counted)

At `F_SYS = 2 MHz`, model includes **1 SYS per fetch byte** (honest shared bus):

| Mix | Gi1 M/s | FE2 M/s | Uplift |
|-----|--------:|--------:|-------:|
| ADD×10 | 0.400 | 0.667 | **+66.7%** |
| MEM pairs | 0.500 | 0.667 | +33.3% |
| balanced | 0.432 | 0.615 | **+42.3%** |

FE1 column in the model is **wishful** (`fe1_possible=False` for every op) — shows the number you wanted, not a buildable schedule.

## Conditions before any FE2 normative proposal

1. CU redesign: drop idx5 idle rows for ALU_REG; state machine **F|E** (+ explicit multi-E).
2. Programmer timing sheet: per-opcode **F count + E count** (abs16, CALL/RET).
3. Lab: ADD F+E at 2 MHz with MBR hold across F→E; MEM address ready after F.
4. WinCUPL Design fits on a future variant (not in this pass).

## Contrast: cpld-ustep

| | [cpld-ustep](../cpld-ustep/) | this study |
|--|------------------------------|------------|
| Idle phases | Hide on USTEP | **Delete** |
| Pedagogy | Keep opcode-varying SYS e-IPC | Prefer **transparent fixed F/E** |
| Dual clock | Related ÷N recommended | **Not required** for FE2 |

## Next steps

1. If pursuing FE2: draft opcode timing sheet + CU state diagram in a follow-up research spike / PLD fork.
2. If insisting on FE1: only via **Harvard / dual-port** machine (new architecture), not Gi1 wiring.
3. Do **not** edit normative multiphase tables until FE2 conditions pass.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial desk study — FE1 No, FE2 Conditional Go |
