# M2b — Datapath and memory (마일스톤 개요)

| Field | Value |
|-------|-------|
| **Milestone** | M2b |
| **Goal** | R0 + MBR→B datapath + SRAM/NOR sockets; manual ADD @ 2 MHz |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [memory-map.md](../hardware/memory-map.md) |

---

## 작업자 안내 — 읽는 순서

| 순서 | 문서 | 하는 일 |
|------|------|---------|
| 1 | [M2b-gpr-datapath.md](M2b-gpr-datapath.md) | **G0→G6** — R0, MBR→B, ALU, 수동 ADD |
| 2 | [M2b-memory.md](M2b-memory.md) | SRAM×2, NOR 소켓, MAP_MODE (G4와 병렬 가능) |

**만들 결과물:** R0 preload + MBR imm → ADD → R0 holds sum @ 2 MHz. SRAM byte R/W OK.

Wiring composite: [breadboard-wiring.md](breadboard-wiring.md).

---

## Prerequisites

- [M2a-cpld-decode.md](M2a-cpld-decode.md) sign-off
- [M1-b3-procedure.md](M1-b3-procedure.md) B3c — `net_clk2` 동작

---

## G0–G6 한눈에

| Step | 문서 | Pass |
|------|------|------|
| G0 | [datapath §G0](M2b-gpr-datapath.md#g0--cpld-in-system) | CPLD LOAD LED |
| G1 | [§G1](M2b-gpr-datapath.md#g1--r0-단독-쓰기) | R0 = DIP |
| G2 | [§G2](M2b-gpr-datapath.md#g2--read-mux) | RA=0 → R0 |
| G3 | [§G3](M2b-gpr-datapath.md#g3--gpr--alu-피연산자) | SUB from R0/MBR |
| G4 | [§G4](M2b-gpr-datapath.md#g4--y--d-버스-r2-쓰기) | Y → D-bus / R0 writeback |
| G5 | [§G5](M2b-gpr-datapath.md#g5--opcodephase--cpld) | CU strobe decode smoke |
| G6 | [§G6](M2b-gpr-datapath.md#g6--수동-cw--2-mhz-add-3-phase) | R0 = sum @ 2 MHz |

---

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Consolidate hub for R0/MBR + memory; P12 wording |
