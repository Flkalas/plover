# P1M1 — P1 bus-TDM + dual 574 operand latch

**Status:** Research (non-normative)  
**Date:** 2026-07-07  
**Parent:** [../README.md](../README.md)

**P1M1** integrates [P1 bus-TDM](../p1-bus-tdm/SUMMARY-REPORT.md) (single `q_bus`, 4-GPR `r_sel`, 4 MHz TDM) with **M1** (second 574 on ALU B, 2-half execute) into one bring-up target.

---

## Executive summary

| Gate | Result |
|------|--------|
| **Pins (CPLD-DP)** | **PASS** — **29/32** (spare 3) |
| **Timing (desk)** | **PASS** — compute half closes ADD/INC/SUB |
| **BOM** | **574 ×5** (PC/MBR/FLG + ALU A + ALU B) |
| **ISA opcode** | unchanged; ph2 execute **500 ns** (2×250 ns) |

**Deliverable:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md) (Korean)

---

## Documents

| File | Content |
|------|---------|
| **[SUMMARY-REPORT.md](SUMMARY-REPORT.md)** | Korean consolidated report |
| [architecture.md](architecture.md) | Block diagram, `op_fetch`, CU handshake |
| [timing-closed.md](timing-closed.md) | Fetch + compute half slack |
| [pin-map.md](pin-map.md) | PLCC-44 vs P1 delta |
| [fsm-isa-delta.md](fsm-isa-delta.md) | ph2a/ph2b, vs M2 |
| [bom-delta.md](bom-delta.md) | IC count table |
| [../variants/p1m1_dp/](../variants/p1m1_dp/) | WinCUPL skeleton |

**Prior art:** [p1-bus-tdm/](../p1-bus-tdm/) · M1 diagrams in [timing-cross-domain.md §6.1](../p1-bus-tdm/timing-cross-domain.md)
