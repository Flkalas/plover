# PE1 architecture (research)

**Non-normative.** Baseline Gi1: von Neumann shared bus ([M3b-fetch-execute.md](../../reference/hw-bringup/M3b-fetch-execute.md)).

## Pipeline

```text
          SYS tick
             |
    +--------v--------+
    |  IF: PC -> PROG |----> IR / operand latch (pipe FF)
    |  (program port) |
    +--------+--------+
             | overlap
    +--------v--------+
    |  EX: ALU / MEM  |----> retire macro (or stall)
    |  (data port)    |
    +-----------------+
```

| Stage | Owns | Clock |
|-------|------|-------|
| **IF** | Program Flash/ROM address = PC (or PC+offset for operand bytes) | SYS |
| **EX** | ALU, data SRAM, PC_LOAD, stack | SYS |
| **ID** | Optional decode inside CPLD-CU (same SYS as IF or EX edge) | — |

Steady state (ALU imm already in pipe): **each SYS retires one macro** while IF loads the next opcode.

## Harvard-like ports (required)

| Port | Device (desk) | Use |
|------|---------------|-----|
| **PROG** | Existing NOR Flash (read-only insn) on dedicated addr/data latch path | IF |
| **DATA** | SRAM via existing 245 path | EX loads/stores / stack |

Same physical Flash chip may stay on the board, but **must not share the data-SRAM cycle** with IF without a stall — PE1 assumes **separate enable / latching** so IF and EX can proceed in parallel when EX is ALU-only.

## Bubble rules (no prediction)

| Event | Action | Desk SYS tax |
|-------|--------|-------------:|
| Fill / first insn | Pipe empty | +1 once (ignore in long mixes) |
| Extra imm/abs **byte** | IF-only operand fetch | +1 per extra byte beyond overlapped opcode |
| **LDA/STA/LDIO/STIO** | DATA port used; IF stalls | +1 mem_stall (default) |
| **Taken BEQ/JMP** | Squash IF; refetch | +1 branch_bubble |
| **Not-taken BEQ** | Continue | 0 |
| **CALL/RET** | Multi-cycle DATA EX | +(stack_sys) visible |

No branch predictor, no delay slot required for the desk model (bubble instead).

## CU

Keep **CPLD FSM-only** spirit: pipe controller is a thin IF/EX/stall state machine in **CPLD-CU**, not Flash CW. idx5 multiphase idle rows are **not** the PE1 schedule.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
