# P12 architecture (research)

**Non-normative.** Base machine = [../pe1/architecture.md](../pe1/architecture.md).  
FE2 serial sheet: [../primitive-one-clock/opcode-fe-table.md](../primitive-one-clock/opcode-fe-table.md).

## Pipeline (unchanged from PE1)

```text
          SYS tick
             |
    +--------v--------+
    |  IF: PC -> PROG |----> IR / operand latch
    |  (program port) |
    +--------+--------+
             | overlap
    +--------v--------+
    |  EX: ALU / MEM  |----> retire (or stall / stretch)
    |  (data port)    |
    +-----------------+
```

Steady ALU stream: **1 SYS / macro** while IF loads the next opcode (imm in prior EX shadow).

## FE2 rules absorbed into EX

| Rule | P12 behavior |
|------|--------------|
| **No idle** | Never reintroduce Gi1 ADD/CMP ph0–1 padding |
| **Optimistic pack** | Same bubble table as PE1 (mem_stall, branch_bubble, …) |
| **Stretch on fail** | Lab unstable at low SYS → **+1** visible stall/EX slot; update sheet |
| **Not clock hope** | Do not “fix” a broken single-EX pack by raising f_SYS first |

## Fallback (not normal mode)

If PROG/DATA isolation cannot hold IF∥EX:

```text
pipe P12  --ports fail-->  serial FE2 (F then E, shared bus)
```

See [fallback-fe2.md](fallback-fe2.md). Do **not** claim shared-bus FE1.

## CU sketch

CPLD-CU thin FSM: IF / EX / stall / stretch / **mode** (pipe vs serial FE2).  
No Flash `$4000` CW. No branch prediction.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
