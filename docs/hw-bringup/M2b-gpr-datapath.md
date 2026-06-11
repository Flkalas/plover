# M2b — GPR ↔ ALU 데이터패스 (G0–G6 상세)

| Field | Value |
|-------|-------|
| **마일스톤** | M2b (데이터패스 절반) |
| **선행** | [M2a](M2a-cpld-decode.md), [M1 B3c](M1-b3-procedure.md#b3c--2-mhz-클록-타이밍-마진) |
| **메모리 배선** | [M2b-memory.md](M2b-memory.md) (병렬 또는 G4 이후) |

CPLD GPR (`q_a`/`q_b`), **REG_SEL** from CW_H, ALU 연결 — **수동** CW로 ADD 3-phase @ 2 MHz.

---

## 1. 신호 흐름

```
CW_H (REG_SEL) ──► CPLD GPR ──► q_a / q_b ──► ALU A/B
                              ▲              │
                              └── Y_OE ── ALU Y ── net_d0..7
```

| 경로 | 넷 |
|------|-----|
| Read A | `net_qa0..7` → `net_a0..7` |
| Read B | `net_qb0..7` → `net_b0..7` |
| Write | `net_y0..7` → `net_d0..7` → 574 D |
| CP 게이트 | `CP_Rn = clk2 AND reg_we AND load_rn` |

---

## 2. 부품 배치

| Ref | Part | 수량 |
|-----|------|------|
| `U_GPR_R0`…`R3` | 74HC574 | 4 |
| `U_GPR_MUX_A/B` | 74HC157 | 4~8 (포트당 157×2) |
| `U_ALU_*` | alu8 | [M1 조립](alu8-assembly-spec.md) |
| `U_CPLD` | ATF1504AS | 1 |

핀 번호: `python -m hwsim pinout 74HC574`

---

## 3. 574 공통 규칙

| 574 핀 | 연결 |
|--------|------|
| D0–D7 | `net_d0..7` (공유 버스) |
| CP | §3.1 게이트 클록 |
| OE | **GND** (Q 항상 구동) |
| VCC/GND | 5 V + 0.1 µF |

### 3.1 쓰기 클록

```text
CP_Rn = net_clk2 AND net_reg_we AND net_load_rn
```

- `net_clk2`: 2 MHz ([M1-b3-procedure](M1-b3-procedure.md))
- 한 사이클에 **LOAD_R 하나만** 1

### 3.2 버스 규칙

동시에 **한 구동원만** `net_d0..7` 구동:

| 구동원 | Enable |
|--------|--------|
| ALU Y | `Y_OE`=1 |
| SRAM | `MEM_RD`=1 (245 경유) |

---

## 4. Read MUX — RA/RB

| RA/RB | 레지스터 |
|-------|----------|
| 00 | R0 |
| 01 | R1 |
| 10 | R2 |
| 11 | R3 |

**브링업 초기:** `RA`, `RB` 를 **DIP 2bit×2** 로 수동.  
**통합 후:** CPLD `REG_SEL0..1` → RA (RB는 설계 확정 시 phase PLA).

157×2 per port (하위/상위 4bit). BOM 부족 시 **포트 A만 MUX**, B는 DIP 직결로 시작.

---

## 5. 단계별 실장 (G0–G6)

각 단계 **Pass 후** 다음으로. 실패 시 이 단계에서 멈추고 고장 분리.

### G0 — CPLD in-system

**작업:** M2a에서 검증한 CPLD를 CPU 보드에 장착. `LOAD_R0..3` 에 LED.

**Pass:** M2a 벤치 워크스루(ADD ph2) LED 동일.

---

### G1 — R0 단독 쓰기

**작업:**

1. `U_GPR_R0` 만 먼저 장착 (R1–R3는 나중).
2. DIP 8bit → `net_d0..7`.
3. `LOAD_R0` 수동 1 (또는 `REG_WE`+opcode/phase로 R0 선택) + **수동 CP** 1회.

**Pass:** R0 Q LED = DIP 패턴.

**팁:** G1에서는 `CP_R0 = button` 으로 단순화 가능. G4부터 `clk2` 게이트.

---

### G2 — Read MUX

**작업:**

1. R0에 알려진 패턴 래치 (예: `0xA5`).
2. MUX A 출력을 **LED 8개**에 연결 (ALU 아직 미연결 가능).
3. DIP `RA=00` → MUX 출력 = R0.

**Pass:** RA=00 일 때 LED = `A5`; RA=01 일 때 R1 값(초기 0).

---

### G3 — GPR → ALU 피연산자

**작업:**

1. MUX A→`net_a*`, MUX B→`net_b*` (또는 B는 DIP).
2. R0=`0x12`, R1=`0x34` 래치.
3. ALU 제어는 **DIP/치트시트** ([opcode](b3-opcode.md)).

**Pass:** SUB smoke — Y LED = `0xDE`.

---

### G4 — Y → D 버스, R2 쓰기

**작업:**

1. `net_y0..7` → `net_d0..7` **짧게** 직결.
2. `Y_OE` DIP로 1 (나중에 CW에서 자동).
3. SUB 결과 확인 후 `LOAD_R2`+`REG_WE`+CP → R2 래치.

**Pass:** R2 Q = 직전 Y.

---

### G5 — opcode/phase → CPLD

**작업:**

1. `net_opc0..3`, `net_ph0..1`, `net_reg_we` 를 CPLD에 연결.
2. [M2a §5.2](M2a-cpld-decode.md#52-add-opcode--phase-워크스루) 워크스루를 **클록 없이** LED로 반복.

**Pass:** ADD ph2 + REG_WE 시 LOAD_R2만 ON.

```bash
python -m hwsim run hw/tests/cpld_gpr_decode.yaml
```

---

### G6 — 수동 CW + 2 MHz ADD 3-phase

**작업:** opcode=`01`(ADD), phase 0→1→2, 각 phase마다 CW DIP 설정 후 **clk2 1 edge**.

수동 CW 표 ([microcode-spec.md](../microcode-spec.md), `pack_control_store.py`):

| Ph | CW (hex) | REG_WE | Y_OE | ALU_OP | MEM | 동작 |
|----|----------|--------|------|--------|-----|------|
| 0 | `14` | 0 | 1 | ADD | — | R0→A |
| 1 | `14` | 0 | 1 | ADD | — | R1→B |
| 2 | `1C` | 1 | 1 | ADD | — | Y→R2 |

**8b CW DIP 해석** (B7..B0): `ALU_OP[3:0]` | `REG_WE` | `Y_OE` | `MEM_RD` | `MEM_WR`

- `0x14` = `0001_0100` → ALU_ADD, Y_OE=1
- `0x1C` = `0001_1100` → ALU_ADD, REG_WE=1, Y_OE=1

**시험 벡터:** R0=`0x12`, R1=`0x34` → ph2 후 R2=`0x46`.

**Pass:** 3 clk edge 후 R2=`46` hex, 중간에 버스 충돌 없음.

```bash
python -m hwsim run hw/tests/regfile_574.yaml
```

---

## 6. ADD 3-phase 타이밍 (@ 2 MHz)

| Ph | REG_WE | Y_OE | LOAD_R* | 동작 |
|----|--------|------|---------|------|
| 0 | 0 | 1 | 0 | R0→A comb |
| 1 | 0 | 1 | 0 | R1→B comb |
| 2 | 1 | 1 | R2 | Y→D, CP↑ |

반주기 250 ns — [alu-opcodes-timing.md](../alu-opcodes-timing.md).

---

## 7. 고장 분리

| 증상 | 확인 |
|------|------|
| A/B 항상 0 | MUX S, 574 OE=GND, RA DIP |
| Y 맞는데 R2 안 바뀜 | LOAD_R2, REG_WE, CP 게이트, D↔Y |
| ADD만 틀림 | CW `14`/`1C`, ALU 제어 |
| 2 MHz 실패 | M1 B3c 스코프 반복 |

---

## 8. 다음

- [M2b-memory.md](M2b-memory.md) — SRAM/NOR/MAP_MODE
- [M3a-control-store.md](M3a-control-store.md) — CW를 Flash에서 자동 로드
