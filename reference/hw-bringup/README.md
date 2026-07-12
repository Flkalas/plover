# Plover hardware bring-up index

> **Normative v1.0 P12:** pipe CU — [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) · [system-architecture.md](../hardware/system-architecture.md).  
> **Legacy:** Gi1 idx5 multiphase M2a/M3a/M3b steps below remain useful wiring history until pipe bring-up is rewritten — [archive/gi1-v1.0-normative/](../../archive/gi1-v1.0-normative/).  
> **실구매 패키지:** [parts-on-hand.md](../project/parts-on-hand.md) · Wiring: [breadboard-wiring.md](breadboard-wiring.md).

**마일스톤 계획:** [archive/MANIFEST.md](../../archive/MANIFEST.md)

초보 작업자도 **문서만 따라** 빵판 CPU를 올릴 수 있도록 단계별 시방서입니다.

> **P12 note:** Target control is **IF\|EX pipe**, not idx5 idle phases. Treat M3a “22 idx5 rows” and M3b multiphase execute as **legacy Gi1** until updated.


---

## 읽는 순서

```mermaid
flowchart LR
  M1[M1 ALU] --> M2a[M2a CPLD FSM]
  M2a --> M2b[M2b 138x2 + memory]
  M2b --> M3a[M3a FSM verify (no Flash CW)]
  M3a --> M3b[M3b fetch FSM]
  M3b --> M4[M4 boot]
  M4 --> M5[M5 E2E]
```

| 순서 | 할 일 | 시작 문서 |
|------|-------|-----------|
| 1 | ALU 납땜 + Y LED | [M1-alu.md](M1-alu.md) → [M1-b3-procedure.md](M1-b3-procedure.md) |
| 2 | CPLD FSM 소각 (WinCUPL CUPL + FIT1504 JED) | [M2a-cpld-decode.md](M2a-cpld-decode.md) |
| 3 | 138×2 · CPLD datapath · SRAM/NOR | [M2b-gpr-memory.md](M2b-gpr-memory.md) · [breadboard-wiring.md](breadboard-wiring.md) |
| 4 | FSM table verify | [M3a-control-store.md](M3a-control-store.md) |
| 5 | ROM fetch + FSM execute | [M3b-fetch-execute.md](M3b-fetch-execute.md) |
| 6 | (PC) 부트 sim | [M4a-boot-sim.md](M4a-boot-sim.md) |
| 7 | 부트 실기 | [M4b-boot-hardware.md](M4b-boot-hardware.md) |
| 8 | netlist 고정 | [M5-cpu-e2e.md](M5-cpu-e2e.md) |

---

## 문서 목록

### M1 — ALU

| 문서 | 내용 |
|------|------|
| [M1-alu.md](M1-alu.md) | 마일스톤 개요 |
| [alu8-assembly-spec.md](alu8-assembly-spec.md) | ALU 12 DIP 단계별 조립 |
| [M1-b3-procedure.md](M1-b3-procedure.md) | B3a/b/c 상세 |
| [b3-opcode.md](b3-opcode.md) | 12 opcode DIP (M1 벤치 전용) |

### M2 — CPU gate

| 문서 | 내용 |
|------|------|
| [M2a-cpld-decode.md](M2a-cpld-decode.md) | CPLD 3fixed + phase FSM ISP |
| [M2b-gpr-memory.md](M2b-gpr-memory.md) | M2b 개요 |
| [M2b-gpr-datapath.md](M2b-gpr-datapath.md) | Gi1 AC (R0) + MBR→ALU B (no decode) |
| [M2b-memory.md](M2b-memory.md) | SRAM·NOR·MAP_MODE |
| [breadboard-wiring.md](breadboard-wiring.md) | 138×2 · CPLD FSM idx5 |

### M3 — Microcode

| 문서 | 내용 |
|------|------|
| [M3a-control-store.md](M3a-control-store.md) | FSM table verify (no Flash CW) |
| [M3b-fetch-execute.md](M3b-fetch-execute.md) | PC · FSM · 첫 ROM 프로그램 |

### M4 / M5

| 문서 | 내용 |
|------|------|
| [M4a-boot-sim.md](M4a-boot-sim.md) | 부트 시뮬 체크리스트 |
| [M4b-boot-hardware.md](M4b-boot-hardware.md) | 빵판 부트 |
| [M5-cpu-e2e.md](M5-cpu-e2e.md) | breadboard composite netlist |

---

## 사전 검증 (개발자)

Breadboard 전 시뮬·회귀 명령: [archive/MANIFEST.md](../../archive/MANIFEST.md).

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | **v1.0** — CPLD FSM + CPLD FSM; no alu8_decode in SoC |
| 2026-06-10 | v1.0 path archived |
| 2026-06-08 | Milestone index M1–M5 |
