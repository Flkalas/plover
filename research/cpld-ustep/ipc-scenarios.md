# CPLD µstep — IPC scenarios (desk model)

**Non-normative.** Numbers from [model/ustep_ipc_model.py](model/ustep_ipc_model.py) at `F_SYS = 2.0 MHz`.

## Formula

```text
macros/s = f_SYS / sys_cycles_per_macro_average
IPC      = macros / sys_cycles
```

`CLK_USTEP` only helps by cutting **SYS-visible** cycles. Sync tax = optional +1 SYS per macro (`sync_latency_sys`).

## Per-macro templates

| Macro | Baseline SYS | USTEP SYS (min) | Notes |
|-------|-------------:|----------------:|-------|
| ADD / CMP | 3 | 1 | Compress idle ph0–1 |
| MEM_LD / MEM_ST | 2 | 2 | Mem-bound |
| BEQ | 3 | 3 | ALU/FLG SYS-bound |
| JMP | 3 | 2 | Mild compression |
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

- **Best case (ALU-only, sync0):** large uplift — shows *why* people want µstep CU.
- **Realistic sync1 + balanced mix:** uplift **~5%** — below a strong Go bar; near the plan’s ≤5% caution zone.
- **Mem-heavy + sync1:** can **regress**.

Desk conclusion for average user code: uplift is **real only if** (a) idle SYS phases are truly removable and (b) synchronizer tax stays **~0**. Breadboard CDC makes (b) unlikely → see [SUMMARY-REPORT.md](SUMMARY-REPORT.md).

## Re-run

```text
cd research/cpld-ustep/model
python ustep_ipc_model.py
python -m pytest test_ustep_ipc_model.py -q
```

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial model numbers |
