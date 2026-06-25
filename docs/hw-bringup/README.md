# Plover hardware bring-up index

> **Normative v1.0:** CPLD FSM idx5 + 138×2 — [system-architecture.md](../hardware/system-architecture.md).  
> **Design rationale:** [research/design-rationale-v1.0.md](../hardware/research/design-rationale-v1.0.md)  
> **실구매 패키지:** [parts-on-hand.md](../project/parts-on-hand.md) · Wiring: [breadboard-wiring.md](breadboard-wiring.md).

**마일스톤 계획:** [implementation-plan-v1.0.md](../project/implementation-plan-v1.0.md) (v1.0 content)  
**아카이브 v1.0:** [prototype-flash-cw/](../archive/prototype-flash-cw/README.md)

초보 작업자도 **문서만 따라** 빵판 CPU를 올릴 수 있도록 단계별 시방서입니다.

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
| 2 | CPLD FSM 소각 | [M2a-cpld-decode.md](M2a-cpld-decode.md) |
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
| [alu8-assembly-spec.md](alu8-assembly-spec.md) | ALU 14 IC 단계별 조립 |
| [M1-b3-procedure.md](M1-b3-procedure.md) | B3a/b/c 상세 |
| [b3-opcode.md](b3-opcode.md) | 12 opcode DIP (M1 벤치 전용) |

### M2 — CPU gate

| 문서 | 내용 |
|------|------|
| [M2a-cpld-decode.md](M2a-cpld-decode.md) | CPLD 3fixed + phase FSM ISP |
| [M2b-gpr-memory.md](M2b-gpr-memory.md) | M2b 개요 |
| [M2b-gpr-datapath.md](M2b-gpr-datapath.md) | CPLD q_a/q_b ↔ ALU (no decode) |
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
| [M4a-boot-sim.md](M4a-boot-sim.md) | pytest·scenario |
| [M4b-boot-hardware.md](M4b-boot-hardware.md) | 빵판 부트 |
| [M5-cpu-e2e.md](M5-cpu-e2e.md) | breadboard composite netlist |

---

## 검증 명령

```bash
# M1
python -m hwsim run hw/tests/alu8_full.yaml

# M2 (v1.0 breadboard)
python -m hwsim run hw/tests/cpld_seq_add.yaml
python -m hwsim run hw/tests/mem_decode_breadboard.yaml

# M3
python tools/pack_control_store.py --hybrid --build-fixtures
python tools/verify_control_store.py --v1.0

# P1 bypass (optional)
python -m hwsim run hw/tests/cpu_cw_direct_add.yaml

# 전체
python -m hwsim run --all
python -m pytest tests/ -q
```

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | **v1.0** — CPLD FSM + CPLD FSM; no alu8_decode in SoC |
| 2026-06-10 | v1.0 path archived |
| 2026-06-08 | Milestone index M1–M5 |
