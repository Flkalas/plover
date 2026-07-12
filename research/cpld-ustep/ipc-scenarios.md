# CPLD µstep — IPC scenarios (desk model)

**Non-normative.** Numbers from [model/ustep_ipc_model.py](model/ustep_ipc_model.py) at `F_SYS = 2.0 MHz`.

## Pedagogy: SYS-visible IPC

```text
IPC      = macros / SYS_cycles
macros/s = f_SYS / SYS_cycles_average
```

**USTEP ticks are control overhead** — they do not appear in the denominator. Learners measure e-IPC on the **datapath clock** they can reason about (bus settle, ALU windows, MEM).

Keeping **opcode-varying SYS costs** (MEM vs ALU vs CALL) is intentional: students discover that e-IPC is not “1.0 for every opcode.” Prefer dual-clock bookkeeping move over single-clock dead-phase compression as the teaching path.

## Clock labels in the model

| Label | Meaning |
|-------|---------|
| **sync0** (`sync_latency_sys=0`) | **Related-clock ÷N** — SYS-aligned strobes; **primary** |
| **sync1** (`sync_latency_sys=1`) | Async dual-osc tax / 2-FF CDC — **fallback** |

## Per-macro templates

| Macro | Baseline SYS | USTEP SYS (min) | Notes |
|-------|-------------:|----------------:|-------|
| ADD / CMP | 3 | 1 | Move control bookkeeping to USTEP; SYS cost = datapath slots (teaching e-IPC) |
| MEM_LD / MEM_ST | 2 | 2 | Mem-bound |
| BEQ | 3 | 3 | ALU/FLG SYS-bound |
| JMP | 3 | 2 | Mild SYS reduction |
| CALL | 8 | 7 | Stack mem dominates |
| RET | 6 | 6 | Stack mem dominates |

## Model results (2026-07-13)

### Single-opcode streams (×10)

| Mix | Mode | IPC | M macro/s | Uplift vs baseline |
|-----|------|----:|----------:|-------------------:|
| ADD | baseline | 0.333 | 0.667 | — |
| ADD | ustep sync0 | 1.000 | 2.000 | **+200%** |
| ADD | ustep sync1 | 0.500 | 1.000 | +50% |
| MEM_LD | baseline | 0.500 | 1.000 | — |
| MEM_LD | ustep sync0 | 0.500 | 1.000 | **0%** |
| MEM_LD | ustep sync1 | 0.333 | 0.667 | **−33%** |

### Mixes

| Mix | Baseline M/s | ustep sync0 | uplift | ustep sync1 | uplift |
|-----|-------------:|------------:|-------:|------------:|-------:|
| alu_heavy | 0.667 | 2.000 | +200% | 1.000 | +50% |
| mem_heavy | 0.833 | 1.250 | +50% | 0.769 | −7.7% |
| control | 0.462 | 0.600 | +30% | 0.462 | 0% |
| **balanced** | **0.727** | **1.231** | **+69%** | **0.762** | **+4.8%** |

## Reading

- **Primary desk bound (related-clock / sync0, balanced):** **+69%** macros/s — relevant under ÷N.
- **ALU-only sync0:** +200% — shows the ceiling when control overhead leaves SYS.
- **sync1 / async tax:** balanced **+4.8%**; mem-heavy can **regress** — why related-clock is the baseline.
- Mem/CALL remain **SYS-bound** even under sync0.

Lab still must prove which baseline SYS cycles are **datapath-real** vs movable bookkeeping — if ADD still needs three SYS settle windows, uplift collapses.

## Re-run

```text
cd research/cpld-ustep/model
python ustep_ipc_model.py
python -m pytest test_ustep_ipc_model.py -q
```

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Pedagogy + sync0=related-clock labeling |
| 2026-07-13 | Initial model numbers |
