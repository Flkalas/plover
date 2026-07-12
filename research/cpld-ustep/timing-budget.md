# CPLD µstep — timing budget (desk)

**Non-normative.** SYS numbers from [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md) · [alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md).

## CLK_SYS (unchanged)

| Quantity | Value |
|----------|------:|
| Frequency | **2.0 MHz** |
| Period | **500 ns** |
| Execute half-cycle | **250 ns** |
| Gi1 ph2 ADD (desk) | **~133 ns** (slack ~117 ns) |
| BEQ path | **212 ns** (slack 38 ns) |

USTEP **does not** relax these paths: ALU, FLG, PC setup still occur in **SYS** windows.

## CLK_USTEP candidates (desk sweep)

| f_USTEP | Period | Role |
|--------:|-------:|------|
| 4 MHz | 250 ns | Match former half-cycle; cheap divide from 4 MHz osc |
| 8 MHz | 125 ns | Primary research target |
| 16 MHz | 62.5 ns | Aggressive; breadboard HC unlikely |

CU-internal decode / wait loops are assumed << one USTEP period on ATF1504 at these rates (desk). **Fit and scope** remain the lab gate.

## When USTEP cannot help

| Path | Why SYS-bound |
|------|----------------|
| MEM_LD / MEM_ST | SRAM/Flash `t_ACC` + CE — one SYS mem cycle minimum each |
| BEQ | 212 ns ALU+FLG+CU+PC in one SYS execute half |
| CALL/RET stack | Multiple SYS `MEM_RD`/`MEM_WR` |
| ph2 ADD execute | Must still open a SYS ALU+`REG_WE` window (~133 ns) |

## When USTEP can help

Baseline **ADD** uses **3 SYS phases** with ph0–1 idle for GPR ([microcode-spec.md](../../reference/hardware/microcode-spec.md) §4). If those idles exist only to keep a single shared clock aligned—not because the bus is busy—an USTEP CU can:

1. Finish internal bookkeeping on USTEP ticks.
2. Issue **one** SYS execute for ALU + `REG_WE`.

Then `sys_cycles_per_ADD` → **1** (plus any sync latency tax).

**Sync tax:** 2-FF synchronizer may add **+0–1 SYS** before the execute strobe is seen — model both `sync_latency_sys ∈ {0,1}`.

## CDC / metastability (breadboard)

| Risk | Mitigation | Residual |
|------|-------------|----------|
| USTEP→SYS strobe metastability | 2-FF sync on request; qualify outputs on SYS | Still fragile on long wires |
| Pulse too narrow for SYS | Stretch to full SYS high | Extra MC |
| DP `reg_we` vs USTEP FSM | DP clocked only by SYS | Required |

Breadboard CDC → default research posture **Conditional Go** even when IPC model looks good.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial timing / CDC desk notes |
