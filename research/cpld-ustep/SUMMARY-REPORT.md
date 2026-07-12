# CPLD µstep clock — summary report

**Date:** 2026-07-13  
**Tier:** Research (non-normative)  
**Model:** [model/ustep_ipc_model.py](model/ustep_ipc_model.py) · [ipc-scenarios.md](ipc-scenarios.md)

## Verdict: **Conditional Go**

Dual-clock CU (`CLK_USTEP` + `CLK_SYS` @ 2 MHz) is **architecturally plausible** and shows **large desk uplift on ALU-heavy code** when synchronizer tax is zero. It is **not** ready as a normative Gi1 change: breadboard **CDC** risk is high, and a **balanced mix with sync_latency_sys = 1** yields only **~+4.8%** macros/s — inside the weak-uplift band.

## Question answers

| # | Question | Desk result |
|---|----------|-------------|
| 1 | IPC / macros/s uplift? | **Yes for ALU-only** (+200% sync0, +50% sync1 on ADD). **Balanced sync0 +69%; sync1 +4.8%.** Mem-only: **0%** or **regression** with sync tax. |
| 2 | Pin / MC cost? | **+1 I/O** (`CLK_USTEP`); desk **+6–16 MC** for sync+wait — within 64 MC / 32 I/O rating ([variants/gi1_cu_ustep/](variants/gi1_cu_ustep/)). |
| 3 | CDC safe on breadboard? | **Unproven** — 2-FF sync assumed; long wires → metastability risk. Forces **Conditional** even when model is green. |

## Evidence snapshot

| Mix | Uplift sync0 | Uplift sync1 |
|-----|-------------:|-------------:|
| ADD×10 | +200% | +50% |
| MEM_LD×10 | 0% | −33% |
| balanced | +69% | **+4.8%** |

Formula reminder: `macros/s = f_SYS / sys_cycles` — faster USTEP alone does not raise throughput.

## Conditions before any normative proposal

1. WinCUPL **Design fits** on `variants/gi1_cu_ustep/` with real `.pld`.
2. Lab CDC plan: scope or pulse-stretch every exported strobe; DP remains SYS-only.
3. Re-measure whether Gi1 ADD ph0–1 are **true idle** (removable) vs **required** MBR/bus settle on the breadboard — if not removable, ADD uplift collapses.
4. Prefer simpler IPC wins first: **dead-phase compression on single CLK** and/or cautious **f_SYS** bump (desk Fmax >3.7 MHz) before dual-clock bring-up.

## Next steps

1. Optional: single-clock phase-compress study (cheaper than CDC).
2. If dual-clock continues: author CU `.pld` fork; fill [fit-report.txt](variants/gi1_cu_ustep/fit-report.txt).
3. Do **not** edit normative microcode phase tables until conditions 1–3 pass.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial desk study — Conditional Go |
