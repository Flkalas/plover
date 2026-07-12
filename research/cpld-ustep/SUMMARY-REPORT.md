# CPLD µstep clock — summary report

**Date:** 2026-07-13  
**Tier:** Research (non-normative)  
**Model:** [model/ustep_ipc_model.py](model/ustep_ipc_model.py) · [ipc-scenarios.md](ipc-scenarios.md)

## Verdict: **Conditional Go** (related-clock dual CU)

Dual-clock CU with **related** `CLK_USTEP` / `CLK_SYS` (same crystal, integer ÷N, no PLL) is the preferred research path. Under **sync0** (related-clock), a **balanced** mix shows **+69%** macros/s — the relevant desk bound. Teaching IPC stays clean: `IPC = macros / SYS_cycles`; USTEP is control overhead.

Still **Conditional** for normative Gi1: need PLD fit, SYS-aligned strobe design, and lab proof that moved cycles are not required MBR/bus settle. Mem/CALL remain SYS-bound. **Do not** prioritize single-clock ADD dead-phase compression (preserves multiphase e-IPC pedagogy).

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | IPC / macros/s under related-clock? | **Yes when bookkeeping leaves SYS.** Balanced **sync0 +69%**; ADD sync0 **+200%**. Mem-only **0%**. sync1 (async tax) balanced only **+4.8%** — fallback, not baseline. |
| 2 | Pin / MC cost? | **+1 I/O** (`CLK_USTEP`); desk **+6–16 MC** for wait/qualify — within 64 MC / 32 I/O ([variants/gi1_cu_ustep/](variants/gi1_cu_ustep/)). |
| 3 | Teaching e-IPC clearer? | **Yes** — SYS-visible denominator + opcode-varying SYS costs. Dual-clock preferred over flattening phases on one CLK. |

## Evidence snapshot

| Mix | Uplift sync0 (related) | Uplift sync1 (async tax) |
|-----|-----------------------:|-------------------------:|
| ADD×10 | +200% | +50% |
| MEM_LD×10 | 0% | −33% |
| balanced | **+69%** | +4.8% |

Formula: `macros/s = f_SYS / sys_cycles` — faster USTEP alone does not raise throughput.

## Conditions before any normative proposal

1. WinCUPL **Design fits** on `variants/gi1_cu_ustep/` with real `.pld`.
2. SYS-aligned strobe qualify from ÷N (sync enable) — not async CDC as the bring-up path.
3. Lab check: which baseline SYS cycles are **datapath-real** vs movable control bookkeeping; if ADD still needs three SYS settle windows, uplift collapses.
4. **Explicit non-priority:** single-clock dead-phase compression as the preferred speed win.

## Next steps

1. Author CU `.pld` fork with related-clock + SYS-aligned qualify; fill [fit-report.txt](variants/gi1_cu_ustep/fit-report.txt).
2. Breadboard: wire undivided OSC to CU `CLK_USTEP`, keep ÷2 as `CLK_SYS`; verify strobe alignment.
3. Do **not** edit normative microcode phase tables until conditions 1–3 pass.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Dialogue sync — related-clock pedagogy; Conditional Go reframed |
| 2026-07-13 | Initial desk study — Conditional Go |
