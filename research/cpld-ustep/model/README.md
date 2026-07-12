# CPLD µstep IPC model (research)

**stdlib only** — scenarios live in `ustep_ipc_model.py` (`SCENARIOS` dict).

## Run

From this directory:

```text
python ustep_ipc_model.py
python -m pytest test_ustep_ipc_model.py -q
```

## Meaning

- **baseline:** each macro costs `baseline_sys_cycles` at `F_SYS = 2 MHz`.
- **ustep:** each macro costs `ustep_sys_cycles + sync_latency_sys` SYS ticks.
- `CLK_USTEP` rate is **not** in the macros/s formula; only SYS-visible cycles matter.
- **`sync_latency_sys=0` (sync0):** **related-clock ÷N** default — SYS-aligned strobes; use this for desk bound.
- **`sync_latency_sys=1` (sync1):** async dual-osc / 2-FF CDC tax — fallback comparison only.

See parent [ipc-scenarios.md](../ipc-scenarios.md) for reported numbers.
