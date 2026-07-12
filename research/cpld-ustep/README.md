# CPLD µstep clock study (dual-clock CU)

**Status:** Research (non-normative)  
**Normative baseline:** single **2.0 MHz** CLK — [cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) · [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md)  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md)

## Questions

1. Does a **CPLD-only `CLK_USTEP`** (4–8 MHz desk) with SoC on **`CLK_SYS` = 2 MHz** raise **user-macro throughput** (macros/s, IPC vs SYS cycles)?
2. What is the **pin / MC** cost of `CLK_USTEP` + strobe synchronizers on ATF1504AS?
3. Is breadboard **CDC** (CU ustep → SYS strobes) acceptable, or does risk force Conditional / No-go?

## Baseline (Gi1 v1.0)

| Item | Value |
|------|------:|
| System clock | **2.0 MHz** (4 MHz ÷ 2) |
| ADD phases | **3** SYS ticks |
| Rough ADD rate | **≈ 0.67 M macro/s** (`2e6 / 3`) |
| Control store | CPLD FSM only — no Flash CW |

## Fixed research decisions

- CU sequencer on **`CLK_USTEP`**; bus / ALU / 574 / CPLD-DP on **`CLK_SYS` = 2 MHz**.
- SoC strobes synchronized into SYS before pin drive.
- First gate = **docs + Python IPC model + PLD spike skeleton** — not breadboard JED burn.

## Deliverables

| File | Role |
|------|------|
| [architecture.md](architecture.md) | Dual-clock CU, wait/ready, sync |
| [timing-budget.md](timing-budget.md) | SYS vs USTEP paths; CDC notes |
| [ipc-scenarios.md](ipc-scenarios.md) | Macro templates + model numbers |
| [model/](model/) | `ustep_ipc_model.py` + pytest |
| [variants/gi1_cu_ustep/](variants/gi1_cu_ustep/) | WinCUPL spike placeholder |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Go / Conditional Go / No-go |

## Out of scope

- Normative edits to `reference/hardware/microcode-spec.md` phase tables
- Breadboard oscillator / CPLD reburn
- Returning Flash `$4000` CW
- Peer “we beat Gigatron” claims in reference prose

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial research tree |
