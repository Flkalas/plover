# PE1 opcode pipe table (desk)

**Non-normative.** Aligns with [architecture.md](architecture.md) bubble rules.  
FE2 serial sheet: [../primitive-one-clock/opcode-fe-table.md](../primitive-one-clock/opcode-fe-table.md).

## Accounting

```text
SYS for one macro ~= 1          # retire slot in steady ALU stream
             + operand_extra    # imm/abs bytes not hidden in overlap
             + mem_stall        # DATA port conflict (default 1 for MEM)
             + branch_bubble    # taken redirect (default 1)
             + stack_extra      # CALL/RET multi-cycle EX
```

Optimistic packing; if lab fails at low clock → **increase stall/bubble** (same policy as FE2 stretch-E).

## Core table

| Op | Steady retire | +operand | +mem | +br taken | +stack | Typical SYS (taken where relevant) |
|----|--------------:|---------:|-----:|----------:|-------:|-----------------------------------:|
| ADD | 1 | 1 (imm) | 0 | 0 | 0 | **2** |
| CMP | 1 | 1 | 0 | 0 | 0 | **2** |
| LDA | 1 | 1 | 1 | 0 | 0 | **3** |
| STA | 1 | 1 | 1 | 0 | 0 | **3** |
| LDIO | 1 | 1 | 1 | 0 | 0 | **3** |
| STIO | 1 | 1 | 1 | 0 | 0 | **3** |
| BEQ nt | 1 | 2 (abs) | 0 | 0 | 0 | **3** |
| BEQ t | 1 | 2 | 0 | 1 | 0 | **4** |
| JMP | 1 | 2 | 0 | 1 | 0 | **4** |
| CALL | 1 | 2 | 0 | 1 | 2 | **6** |
| RET | 1 | 0 | 0 | 1 | 2 | **4** |
| STA16 | 1 | 2 | 1 | 0 | 0 | **4** |
| HALT | 1 | 0 | 0 | 0 | 0 | **1** |

Notes:

- **operand_extra:** opcode byte overlapped with previous EX when possible; remaining format bytes still cost IF cycles (8-bit PROG).
- **ADD/CMP SYS=2** in a cold pipe (opcode+imm); in a long ALU stream after fill, model may treat sustained rate closer to **1 SYS/macro** if imm is fetched in the shadow of prior EX — see model `alu_stream` mode.
- CALL stack_extra=2: two DATA writes (ret PC) beyond redirect; RP update folded into those in optimistic desk.

## vs FE2 / Gi1 (same ops, rough)

| Op | Gi1 F+E (model) | FE2 opt. | PE1 typical |
|----|----------------:|---------:|------------:|
| ADD | 5 | 3 | **2** (stream → ~1) |
| LDA | 4 | 3 | **3** |
| JMP | 4 | 4 | **4** |
| CALL | 8 | 6 | **6** |

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
