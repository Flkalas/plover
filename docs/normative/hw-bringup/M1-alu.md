# M1 — ALU + 574 accumulator bring-up (마일스톤 개요)

| Field | Value |
|-------|-------|
| **Milestone** | M1 · [implementation-plan](../project/implementation-plan-v1.0.md) §3 |
| **Goal** | 12-opcode `alu8` 검증 + 574 래치 @ 2 MHz |
| **Breadboard status** | Pending |

---

## 작업자 안내 — 무엇을 읽고 무엇을 만드나

| 순서 | 문서 | 하는 일 |
|------|------|---------|
| 1 | [alu8-assembly-spec.md](alu8-assembly-spec.md) | ALU 14 IC를 **단계별로** 납땜·배선 (0→4단계, 매단계 LED 확인) |
| 2 | **[M1-b3-procedure.md](M1-b3-procedure.md)** | B3a → B3b → B3c 검증 (Y LED, 574 래치, 2 MHz) |
| 3 | [b3-opcode.md](b3-opcode.md) | 12 opcode마다 **어느 DIP를 ON/OFF** 할지 표 |

**만들 결과물:** SUB/XOR/INC smoke가 Y LED에서 맞고, B3c에서 2 MHz로 Q가 Y를 따라감.

---

## Scope

| 포함 | 제외 |
|------|------|
| ALU8 (Phase B2, 14 DIP) | CPLD GPR (M2) |
| 574 ACC 1개 (B3b/c) | ROM, microcode |
| 2 MHz `net_clk2` | 부트, Mailbox |

---

## Prerequisites

- [BOM.md](../../BOM.md) **ALU (B3a):** 283×2, 153×8, 157×2, 04×2
- **B3b/c 추가:** 574×1, 74HC74, 4 MHz OSC
- (`74HC08`/`74HC32`는 v1.0 ALU에 **미사용** — M2 CPU glue)
- 5 V, 0.1 µF/IC, 10 µF bulk
- 배선 **전**:

---

## Phase 요약

| Phase | 추가 | 상세 |
|-------|------|------|
| **B3a** | ALU + Y LED | [M1-b3-procedure.md § B3a](M1-b3-procedure.md#b3a--alu만-y-led-클록-없음) |
| **B3b** | +574, 수동 CP | [M1-b3-procedure.md § B3b](M1-b3-procedure.md#b3b--574-acc-수동-cp) |
| **B3c** | +2 MHz | [M1-b3-procedure.md § B3c](M1-b3-procedure.md#b3c--2-mhz-클록-타이밍-마진) |

---

## M1 sign-off (마일스톤 완료 체크리스트)

작업 리더가 아래를 전부 체크한 뒤 M2로 넘깁니다.

- [ ] [조립 시방](alu8-assembly-spec.md) **단계 0~4 (B3a ALU)** 완료
- [ ] [M1-b3-procedure.md](M1-b3-procedure.md) B3b/B3c 완료
- [ ] B3a smoke: SUB `12−34=DE`, XOR `12^34=26`, INC `12→13`
- [ ] (권장) opcode 치트시트 12종
- [ ] B3b: CP 1회 후 Q = Y (SUB/XOR/INC)
- [ ] B3c: SUB 벡터 ≥2 클록 @ 목표 주파수
- [ ] 스코프 마진 기록 또는 derated 클록 문서화
- [ ] `alu8_full` + `alu_b3_latch` pre-flight sim PASS

---

## 다음 마일스톤

→ [M2a-cpld-decode.md](M2a-cpld-decode.md)
