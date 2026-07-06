# Gi1 — Gigatron-style AC + MBR operand path

**Status:** Research (non-normative)  
**Date:** 2026-07-07  
**Parent:** [../README.md](../README.md)

**Gi1** keeps rev G **2 MHz / 250 ns** execute budget while adopting a **Gigatron-like** programming model: single **AC (R0)** in CPLD-DP, **immediate operand from MBR 574** to ALU B, **ADD/CMP writeback to R0**, **TFR opcodes removed**.

---

## Executive summary

| Gate | Result |
|------|--------|
| **Pins (CPLD-DP)** | **PASS** — desk **~18/32** (spare 14) |
| **Timing (ph2)** | **PASS** — ADD Y≈133 ns @ 250 ns |
| **BOM** | **574 ×3** unchanged vs rev G |
| **ISA** | AC-centric; **no TFR**; 4-GPR vision dropped |

**Deliverable:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md) (Korean)

---

## Documents

| File | Content |
|------|---------|
| **[SUMMARY-REPORT.md](SUMMARY-REPORT.md)** | Korean consolidated report |
| [architecture.md](architecture.md) | Block diagram, Gigatron mapping |
| [timing-closed.md](timing-closed.md) | ph2 slack @ 250 ns |
| [isa-delta.md](isa-delta.md) | Opcode and program model |
| [fsm-microcode-delta.md](fsm-microcode-delta.md) | idx5, MBR hold |
| [pin-map.md](pin-map.md) | PLCC-44 vs rev G |
| [bom-delta.md](bom-delta.md) | FF / MC / wiring |
| [gigatron-benchmark.md](gigatron-benchmark.md) | vs Gigatron / Isetta / rev G |
| [../variants/gi1_dp/](../variants/gi1_dp/) | WinCUPL skeleton |

**Contrast:** [P1 bus-TDM](../p1-bus-tdm/) (4-GPR TDM) · [P1M1](../p1m1-dual574/) (dual 574, 500 ns ph2)
