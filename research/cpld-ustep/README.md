# CPLD µstep clock study (dual-clock CU)

**Status:** Research (non-normative)  
**Normative baseline:** single **2.0 MHz** CLK — [cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) · [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md)  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md)

## Questions

1. Under a **related-clock** pair (`CLK_USTEP` / `CLK_SYS` from one crystal, integer ÷N), does moving control bookkeeping to USTEP raise **macros/s** when IPC is counted on **SYS-visible** cycles only?
2. What are the **pin / MC** costs of `CLK_USTEP` + SYS-aligned strobe qualify on ATF1504AS?
3. Does dual-clock make **teaching e-IPC** clearer (`IPC = macros / SYS_cycles`) while keeping **opcode-varying SYS costs**?

## Baseline (Gi1 v1.0)

| Item | Value |
|------|------:|
| System clock | **2.0 MHz** (4 MHz ÷ 2) |
| ADD phases | **3** SYS ticks |
| Rough ADD rate | **≈ 0.67 M macro/s** (`2e6 / 3`) |
| Control store | CPLD FSM only — no Flash CW |

## Fixed research decisions

- **Related clocks (primary):** same OSC → integer divide — e.g. 4 MHz → `CLK_SYS` = ÷2 (2 MHz), `CLK_USTEP` = 4 MHz. **No PLL.**
- CU sequencer on **`CLK_USTEP`**; bus / ALU / 574 / CPLD-DP on **`CLK_SYS`**.
- SoC strobes asserted only on **SYS-aligned** USTEP edges (sync enable) — not async dual-osc CDC as the baseline.
- **IPC (teaching):** `IPC = macros / SYS_cycles`, `macros/s = f_SYS / SYS_cycles`. USTEP ticks = control overhead.
- **Do not** prioritize single-clock ADD dead-phase compression (preserves multiphase e-IPC lesson for learners).
- Async 2-FF CDC = **fallback** only if clocks are unrelated.

## Deliverables

| File | Role |
|------|------|
| [architecture.md](architecture.md) | Related-clock CU, SYS-aligned strobes |
| [timing-budget.md](timing-budget.md) | ÷N first; async CDC demoted |
| [ipc-scenarios.md](ipc-scenarios.md) | Pedagogy + model numbers (sync0 = related) |
| [model/](model/) | `ustep_ipc_model.py` + pytest |
| [variants/gi1_cu_ustep/](variants/gi1_cu_ustep/) | WinCUPL spike placeholder |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Conditional Go (related-clock) |

## Out of scope

- Normative edits to `reference/hardware/microcode-spec.md` phase tables
- Breadboard oscillator / CPLD reburn
- Returning Flash `$4000` CW
- Peer “we beat Gigatron” claims in reference prose

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Dialogue sync — related-clock + SYS-IPC pedagogy |
| 2026-07-13 | Initial research tree |
