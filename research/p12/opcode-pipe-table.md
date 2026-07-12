# P12 opcode pipe table (desk)

**Non-normative.** Optimistic costs match [../pe1/opcode-pipe-table.md](../pe1/opcode-pipe-table.md).  
Stretch policy from [../primitive-one-clock/opcode-fe-table.md](../primitive-one-clock/opcode-fe-table.md).

## Accounting

```text
SYS ~= 1                  # retire slot
     + operand_extra
     + mem_stall
     + branch_bubble      # taken
     + stack_extra
     + stretch            # lab fail once (P12 stretch mode)
```

## Core table (optimistic = PE1)

| Op | Steady | +op | +mem | +br t | +stack | Typical SYS | Stretch if lab fails |
|----|-------:|----:|-----:|------:|-------:|------------:|----------------------|
| ADD | 1 | 1 | 0 | 0 | 0 | **2** (stream→1) | rarely; keep E=1 |
| CMP | 1 | 1 | 0 | 0 | 0 | **2** (stream→1) | split FLG if late |
| LDA | 1 | 1 | 1 | 0 | 0 | **3** | +1 mem/EX → **4** |
| STA | 1 | 1 | 1 | 0 | 0 | **3** | +1 → **4** |
| LDIO | 1 | 1 | 1 | 0 | 0 | **3** | +1 → **4** |
| STIO | 1 | 1 | 1 | 0 | 0 | **3** | +1 → **4** |
| BEQ nt | 1 | 2 | 0 | 0 | 0 | **3** | +1 EX → **4** |
| BEQ t | 1 | 2 | 0 | 1 | 0 | **4** | +1 bubble/EX → **5** |
| JMP | 1 | 2 | 0 | 1 | 0 | **4** | rarely |
| CALL | 1 | 2 | 0 | 1 | 2 | **6** | +1 stack → **7** |
| RET | 1 | 0 | 0 | 1 | 2 | **4** | +1 → **5** |
| STA16 | 1 | 2 | 1 | 0 | 0 | **4** | +1 → **5** |
| HALT | 1 | 0 | 0 | 0 | 0 | **1** | — |

Model `p12_stretch` applies the first stretch on **LDA/STA/BEQ(taken)/CALL/RET** (+1 each).

## vs peers (rough)

| Op | Gi1 | FE2 opt. | PE1 / P12 opt. | P12 stretch |
|----|----:|---------:|---------------:|------------:|
| ADD stream | 5 | 3 | **1** | **1** |
| LDA | 4 | 3 | **3** | **4** |
| BEQ t | 5 | 4 | **4** | **5** |
| CALL | 8 | 6 | **6** | **7** |

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
