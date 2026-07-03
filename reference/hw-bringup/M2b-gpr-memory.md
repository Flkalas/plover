# M2b — GPR, datapath, and memory (마일스톤 개요)

| Field | Value |
|-------|-------|
| **Milestone** | M2b |
| **Goal** | GPR×4 + MUX + ALU + SRAM + NOR 소켓; 수동 ADD @ 2 MHz |
| **pre-flight sim** | `regfile_574`, `alu8_full`, `cpld_gpr_decode`, `mem_decode` |

---

## 작업자 안내 — 읽는 순서

| 순서 | 문서 | 하는 일 |
|------|------|---------|
| 1 | [M2b-gpr-datapath.md](M2b-gpr-datapath.md) | **G0→G6** — 574, MUX, ALU, 수동 CW ADD |
| 2 | [M2b-memory.md](M2b-memory.md) | SRAM×2, NOR 소켓, MAP_MODE (G4와 병렬 가능) |

**만들 결과물:** R0=`12`, R1=`34` 넣고 수동 CW/phase로 ADD 후 R2=`46` @ 2 MHz. SRAM byte R/W OK.

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
| G3 | [§G3](M2b-gpr-datapath.md#g3--gpr--alu-피연산자) | SUB from GPR |
| G4 | [§G4](M2b-gpr-datapath.md#g4--y--d-버스-r2-쓰기) | R2 = Y |
| G5 | [§G5](M2b-gpr-datapath.md#g5--opcodephase--cpld) | LOAD_R2 decode |
| G6 | [§G6](M2b-gpr-datapath.md#g6--수동-cw--2-mhz-add-3-phase) | R2=`46` |

메모리: [M2b-memory.md](M2b-memory.md).

---

## M2b sign-off

- [ ] G1–G6 전부 Pass
- [ ] [memory sign-off](M2b-memory.md#5-m2b-메모리-sign-off-데이터패스와-합산)
- [ ] pre-flight sim 4종 PASS

---

## 다음

→ [M3a-control-store.md](M3a-control-store.md)
