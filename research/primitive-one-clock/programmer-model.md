# Programmer timing model (research)

**Non-normative.** Contrast with Gi1 multiphase CU.

## What “full control” means here

The programmer should be able to say:

```text
this instruction costs N SYS clocks
```

where **N is in the ISA/timing sheet**, not discovered by reading idle rows in an internal phase table.

| Model | What the programmer counts | Hidden? |
|-------|----------------------------|---------|
| **Gi1 today** | Varies by opcode (ADD 3 exec phases, …); fetch separate in bring-up narrative | **Yes** — idle ph0–1 on ADD/CMP |
| **FE1** | **1 SYS** for entire fetch+execute of one insn | No (if achievable) |
| **FE2** | **2 SYS** fixed: F then E (exceptions listed explicitly) | No idle; multi-slot ops called out |

## Gi1 problem (from owner intent)

```text
ADD macro
  SYS ph0  cu / ---     <- looks like "nothing" but burns a clock
  SYS ph1  cu / ---
  SYS ph2  cu / DP      <- real work
```

ISA still chooses ADD; **clock cost is CU policy**. That breaks “1 work ≈ 1 clock” intuition.

## FE1 programmer sheet (aspirational)

| Insn class | SYS cost |
|------------|---------:|
| All single-bus ops | **1** |

Only credible with Harvard/dual-port, collapsed ISA, or a clock slow enough to serialize impossible overlaps — see [bus-timing-feasibility.md](bus-timing-feasibility.md).

## FE2 programmer sheet (primitive regression)

| Slot | Does |
|------|------|
| **F** | PC→mem → IR (+ start operand bytes as defined) |
| **E** | One datapath window: ALU **or** one MEM **or** PC load |

| Insn | F | E | Notes |
|------|--:|--:|------|
| ADD/CMP imm | 1 | 1 | Drop Gi1 idle; imm must be ready for E (may need wider F or prior byte) |
| LDA/STA | 1 | 1 | Address in MBR from F; one MEM in E — **or** FE2+ if addr+data need two bus cycles |
| JMP | 1 | 1 | Abs16 may need extra F bytes (programmer-visible) |
| CALL/RET | 1 | **k** | Stack mem = **documented** multi-E, not idle padding |

Rule: **no blank SYS for CU bookkeeping.** Extra SYS only when the bus/ALU/PC actually moves.

## IPC / macros/s

```text
IPC      = macros / SYS_cycles
macros/s = f_SYS / SYS_cycles_average
```

Same formulas as ustep research; different **cost table** (delete idle, do not move to USTEP).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
