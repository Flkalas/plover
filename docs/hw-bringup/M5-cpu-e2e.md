# M5 — Integrated CPU netlist E2E (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M5 |
| **Goal** | 빵판 배선을 `cpu.yaml` + hwsim으로 **재현 가능**하게 고정 |
| **Status** | Stub |
| **선행** | M2b–M4b breadboard smoke |

---

## 1. 왜 M5인가

M1–M4b는 **수동 단계**로 CPU를 올립니다. M5는 그 결과를:

- netlist 블록 병합
- hwsim/cyclesim E2E 테스트

로 **회귀 가능**하게 만듭니다. 이후 netlist/배선 변경 시 자동 gate.

---

## 2. 현재 stub

```1:9:hw/netlist/blocks/cpu.yaml
version: 1
block: cpu
description: "v0.1 CPU datapath — 574×4 GPR + ATF1504AS system CPLD (composite stub)"
includes:
  - regfile_574.yaml
  - cpld_system_ctrl.yaml
notes: |
  Full SoC netlist merges ALU8, addr_mux, sram256_dual, nor_flash.
  Generate with: python tools/gen_cpu_netlist.py
```

---

## 3. 작업 패키지 (순서대로)

### M5.1 — `pc_phase.yaml`

| 넷 | 설명 |
|----|------|
| `net_pc0..15` | program counter |
| `net_ph0..1` | micro phase |
| `net_ir0..7` | instruction register |

**Pass:** hwsim에서 RESET 후 PC=`0` stimulus 반영.

### M5.2 — `addr_mux.yaml`

| 입력 | 출력 |
|------|------|
| PC | instruction fetch |
| `{opcode,phase}` + `$4000` | CW fetch |
| effective addr | LDA/STA |

**Pass:** mux select 벡터 3종 시뮬.

### M5.3 — `sram256_dual.yaml` / `nor_flash.yaml`

[M2b-memory.md](M2b-memory.md) 배선을 YAML화. CS를 CPLD stub에 연결.

**Pass:** `mem_decode` 유지 PASS.

### M5.4 — `gen_cpu_netlist.py`

```bash
python tools/gen_cpu_netlist.py   # TBD — 스크립트 추가 시
```

출력: 갱신된 `hw/netlist/blocks/cpu.yaml`.

### M5.5 — `hw/tests/cpu_e2e.yaml`

ROM 이미지 ([M3b §F1](M3b-fetch-execute.md#f1--instruction-fetch)):

```
02 42   ; LDA $42
01 00   ; ADD $00
0A      ; HALT
```

**expect:** HALT 시점 GPR 스냅샷 = M3b F6 기대값.

### M5.6 — cyclesim parity

```bash
python -m cyclesim run hw/tests/cpu_e2e.yaml   # TBD
```

---

## 4. M5 sign-off

- [ ] `cpu.yaml`에 §3 블록 전부 include
- [ ] `cpu_e2e.yaml` hwsim PASS
- [ ] M3b 빵판 F6 trace와 hwsim GPR 일치 (스크린샷/로그 보관)
- [ ] [hw-sim.md](../hw-sim.md)에 regen 명령 문서화
- [ ] `implementation-plan-v0.1.md` §2 M5 행 갱신

---

## 5. 작업자 노트

M5는 **새 납땜 단계가 아님** — M1–M4b에서 이미 동작하는 보드를 기준으로 netlist를 **역작성**합니다. 배선 변경 시 M5 gate를 먼저 깨뜨리고 수정하는 워크플로를 씁니다.
