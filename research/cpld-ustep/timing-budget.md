# CPLD µstep — timing budget (desk)

**Non-normative.** SYS numbers from [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md) · [alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md).

## CLK_SYS (unchanged normative target)

| Quantity | Value |
|----------|------:|
| Frequency | **2.0 MHz** |
| Period | **500 ns** |
| Execute half-cycle | **250 ns** |
| Gi1 ph2 ADD (desk) | **~133 ns** |
| BEQ path | **212 ns** |

USTEP does **not** relax ALU/BEQ SYS windows.

## Related-clock ÷N (primary)

| Example | CLK_USTEP | CLK_SYS | Ratio |
|---------|----------:|--------:|------:|
| From 4 MHz OSC | 4 MHz | 2 MHz (÷2) | 2× |
| From 12 MHz OSC | 6 MHz (÷2) | 2 MHz (÷6) | 3× |

Under related clocks:

- Assert strobes only on **SYS-aligned** USTEP edges.
- Model **`sync_latency_sys = 0`** (sync0 tables in [ipc-scenarios.md](ipc-scenarios.md)).
- **No PLL** — HC dividers only.

## When USTEP cannot cut SYS cycles

| Path | Why SYS-bound |
|------|----------------|
| MEM_LD / MEM_ST | Memory `t_ACC` |
| BEQ | 212 ns path in one SYS execute half |
| CALL/RET stack | Multiple SYS `MEM_*` |
| ALU execute | Still needs one SYS ALU + `REG_WE` window |

## What USTEP is for (pedagogy + control)

- Hold **control bookkeeping** off the SYS IPC denominator.
- Leave **datapath SYS slots** opcode-dependent so e-IPC still varies (learners discover this).
- Do **not** treat “delete ADD ph0–1 on a single shared CLK” as the preferred speed strategy.

## Fallback: async CDC

Unrelated oscillators → 2-FF sync / pulse stretch → **`sync_latency_sys ≥ 1`** (sync1 tables). Breadboard metastability risk. Demoted vs related-clock.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Related-clock first; pedagogy note; async demoted |
| 2026-07-13 | Initial timing / CDC desk notes |
