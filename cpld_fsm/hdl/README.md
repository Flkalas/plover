# Plover CPLD FSM — WinCUPL build (rev G dual ATF1504AS)

Target: **2× ATF1504AS-10JU44** — **CPLD-CU** (idx5 + strobes) + **CPLD-DP** (GPR + full `q`).

**Normative:** [reference/hardware/cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) · JTAG: [cpld-dual-jtag.md](../../reference/hardware/cpld-dual-jtag.md)

## Sources

| File | Role |
|------|------|
| [`system_ctrl_cu.pld`](system_ctrl_cu.pld) | CPLD-CU — phase FSM, strobes, G-IC |
| [`system_ctrl_dp.pld`](system_ctrl_dp.pld) | CPLD-DP — GPR, TFR mux, full `q_a`/`q_b` |
| [`ctrl_lut.inc`](ctrl_lut.inc) | **Generated** idx5 LUT (CU only) |
| [`gen_ctrl_lut.py`](gen_ctrl_lut.py) | Codegen from `fsm_table.py` |
| [`build-wincupl.ps1`](build-wincupl.ps1) | CUPL + FIT1504 — **both JEDs** |
| [`verify-cpld.ps1`](verify-cpld.ps1) | Pre-flash Tier 0–2 gate |
| [`g_dual_integration.py`](g_dual_integration.py) | Rev G CU/DP golden model (TFR pytest) |

TFR comb (`tfr_valid`) and G-IC merge are in `system_ctrl_cu.pld`; xfer mux in `system_ctrl_dp.pld`.

## JTAG

Daisy chain: programmer → **CU** (TDI first) → **DP** → programmer TDO. Program **CU JED before DP**.

## Pre-flash gate

Run `verify-cpld.ps1` — codegen, pytest, optional WinCUPL fit for both chips.

**Superseded:** monolithic Tier C — [archive/tier-c-single-cpld/README.md](../../archive/tier-c-single-cpld/README.md). GPR-FSM fit study — [archive/fit-study-gpr-fsm.tar.gz](../../archive/fit-study-gpr-fsm.tar.gz) (stub: [fit-study/README.md](../fit-study/README.md)).
