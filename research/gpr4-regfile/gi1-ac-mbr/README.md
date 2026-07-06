# Gi1 — Gigatron-style AC + MBR operand path

**Status:** **Absorbed into v1.0 reference (2026-07)** — normative truth in [reference/hardware/](../../reference/hardware/) and [plover-whitepaper.md](../../plover-whitepaper.md). This folder remains design notes and PLD spikes.  
**Parent:** [../README.md](../README.md)

**Gi1** keeps rev G **2 MHz / 250 ns** execute budget while adopting a **Gigatron-like** programming model: single **AC (R0)** in CPLD-DP, **immediate operand from MBR 574** to ALU B, **ADD/CMP writeback to R0**, **TFR opcodes removed**.

---

## Executive summary

| Gate | Result |
|------|--------|
| **Pins (CPLD-DP)** | **PASS** — desk **17/32** (spare 15) |
| **Pins (CPLD-CU)** | **PASS** — desk **~21/32** (spare ~11) |
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
| **[cpld-dual-delta.md](cpld-dual-delta.md)** | **CPLD-CU / CPLD-DP 역할·핀·G-IC** |
| **[io-pin-allocation.md](io-pin-allocation.md)** | **PLCC 핀 분배·단일 칩 통합 조사** |
| **[soc-strobes-gi1.md](soc-strobes-gi1.md)** | **CU SoC 14출력 구성·Gi1 필요성** |
| [timing-closed.md](timing-closed.md) | ph2 slack @ 250 ns |
| [isa-delta.md](isa-delta.md) | Opcode and program model |
| [fsm-microcode-delta.md](fsm-microcode-delta.md) | idx5, MBR hold |
| [pin-map.md](pin-map.md) | PLCC-44 vs rev G |
| [bom-delta.md](bom-delta.md) | FF / MC / wiring |
| [gigatron-benchmark.md](gigatron-benchmark.md) | vs Gigatron / Isetta / rev G |
| [../variants/gi1_dp/](../variants/gi1_dp/) | WinCUPL skeleton (DP) |
| [../variants/gi1_cu/](../variants/gi1_cu/) | CU idx5 change memo |

**Contrast:** [P1 bus-TDM](../p1-bus-tdm/) (4-GPR TDM) · [P1M1](../p1m1-dual574/) (dual 574, 500 ns ph2)
