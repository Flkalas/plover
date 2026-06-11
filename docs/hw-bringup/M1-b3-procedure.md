# M1 — B3a / B3b / B3c 상세 절차 (ALU + 574 + 2 MHz)

| 항목 | 내용 |
|------|------|
| **마일스톤** | M1 |
| **선행** | 없음 (첫 하드웨어 단계) |
| **완료 체크** | [M1-alu.md](M1-alu.md) § sign-off |
| **조립 상세** | [ALU8 단계별 조립](alu8-assembly-spec.md) (14 IC, 한국어) |
| **Opcode DIP** | [b3-opcode.md](b3-opcode.md) |

빵판 절차 3단계: **B3a** (조합 Y) → **B3b** (수동 래치) → **B3c** (2 MHz 클록).  
배선 전 **hwsim**으로 동작을 확인합니다.

| Phase | Netlist | hwsim |
|-------|---------|-------|
| **B3a** | [`alu8.yaml`](../../hw/netlist/blocks/alu8.yaml) | `alu8_full.yaml` |
| **B3b** | [`alu_b3.yaml`](../../hw/netlist/blocks/alu_b3.yaml) | `alu_b3_latch.yaml` |
| **B3c** | [`alu_b3_clock.yaml`](../../hw/netlist/blocks/alu_b3_clock.yaml) | 배선만 — **스코프** @ 2 MHz |

목표 클록 (B3c): **2 MHz** — 주기 500 ns, posedge 전 조합 예산 **250 ns**.

**배선 전 필수:**

```bash
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim export-schematic hw/netlist/blocks/alu8.yaml -o build/alu8-schematic.svg --html
```

`build/alu8-schematic.html` — IC 14개 배선도. 제어 넷은 주황색.

---

## 공통 — 전원·디커플링

- **0.1 µF / IC 1개**, 5 V 레일에 **10 µF** 벌크.
- 제어 입력: [opcode 치트시트](b3-opcode.md). 시트에 없는 제어 넷은 **GND** (VCC 예외만 시트 참조).
- **INC/DEC (B3a):** `net_b0..7` 을 피연산자로 쓰지 말 것. `153_B` INC/DEC 상수는 **하드와이어** — **`b_const_sel` + `b_sel`만** 설정. 치트시트 `b_const_bit1..7` 열은 hwsim parity (선택 `alu_decode` 단계에서만 물리 DIP).

---

## B3a — ALU만, Y LED (클록 없음)

**목표:** 574·클록 없이 12 opcode 조합 논리 검증.

### 부품

| Phase | 추가 IC | 누적 (ALU+ACC+clk) |
|-------|---------|---------------------|
| **B3a** | ALU 코어 **14** | 14 |
| **B3b** | +574×1 | 15 |
| **B3c** | +4 MHz OSC, +74HC74 (÷2) | 17+ |

참조: [alu8.md](../../hw/netlist/blocks/alu8.md) · [조립 시방](alu8-assembly-spec.md)

B3a: 574, OSC, 74HC74 **없음**.

### 배선 (순서대로)

1. **전원** — 5 V, GND, 모든 DIP에 디커플링.
2. **ALU 코어** — [`alu8.yaml`](../../hw/netlist/blocks/alu8.yaml) ref 순서:  
   283 → 04 BINV → **153_B** → 283 → **153_L** → **157_YBP** (sum vs logic → Y).  
   CMP 플래그는 SUB 경로 (`net_y`, `net_c_hi`).
3. **피연산자** — DIP ×16: `net_a0..7`, `net_b0..7` (INC/DEC 시 B 무시).
4. **제어** — 치트시트대로 DIP/타이: `cin`, `153_s0/s1`, `b_sel`, `b_const_sel`, `net_lgc0..3`.  
   SUB/CMP: `b_sel=1`, `cin=1`. (B3a: `b_const_bit*` 넷 없음 — INC/DEC는 `b_const_sel`+`b_sel`만)
5. **출력** — `net_y0..7` → LED ×8 (330 Ω~1 kΩ). 선택: `net_c_hi` LED.

### 작업 절차

1. [치트시트](b3-opcode.md)에서 opcode 행을 찾는다.
2. A, B, 제어 DIP/타이를 설정한다.
3. **Y LED**를 읽는다 — 클록 없음, 조합 안정 후 ~µs 이내.

### 첫 전원 smoke

| Op | A | B | 기대 Y |
|----|---|---|--------|
| SUB | `0x12` | `0x34` | `0xDE` |
| XOR | `0x12` | `0x34` | `0x26` |
| INC | `0x12` | — | `0x13` |

### 완료 기준 (B3a)

- [ ] ALU IC 전원·디커플링 완료
- [ ] smoke 3종 Y LED 일치
- [ ] (권장) 치트시트 12 opcode 전부

### Gate

```bash
python -m hwsim run hw/tests/alu8_full.yaml
```

---

## B3b — +574 ACC, 수동 CP

**목표:** 수동 클록 1펄스로 조합 **Y**를 **Q**에 래치.

### 추가 부품

| 블록 | IC |
|------|-----|
| 574 ACC | +1 — `U_REG_574_ACC` |

### 추가 배선

| 연결 | 비고 |
|------|------|
| `net_y0..7` → `574 D0..7` | 조합 → 래치 D |
| `574 OE` → GND | 항상 출력 |
| `574 CP` ← **푸시버튼** | 5 V→CP; 10 kΩ 풀다운; 0.1 µF 디바운스 |
| `574 Q0..7` → **Q LED ×8** | Y LED와 비교 유지 |

### 한 사이클 (반복 연습)

1. B3a와 같이 A, B, 제어 설정.
2. **Y LED** 안정 확인.
3. **CP 버튼 1회** (0→1→0).
4. **Q LED = Y**.

### Gate

```bash
python -m hwsim run hw/tests/alu_b3_latch.yaml
```

### 완료 기준 (B3b)

- [ ] SUB/XOR/INC: CP 후 Q = Y
- [ ] CP 전 Q는 이전 값 유지

---

## B3c — +2 MHz 클록, 타이밍 마진

**목표:** 2 MHz 연속 래치; setup 마진 확인 (스코프).

### 추가 부품

| 블록 | IC |
|------|-----|
| 클록 | +2 — 4 MHz OSC + 74HC74 ([`clock.yaml`](../../hw/netlist/blocks/clock.yaml)) |

B1 클록 보드 재사용 가능. **`net_clk2` → `574 CP`** (푸시버튼 제거).

### 배선 변경

| 항목 | 변경 |
|------|------|
| CP | 버튼 제거 → **`net_clk2`** |
| OSC | 4 MHz → 74HC74 ÷2 → `net_clk2` |

### 오실로스코프 (2 MHz, 실기만)

| 측정 | CH-A | CH-B | Pass |
|------|------|------|------|
| 조합 안정 | `net_y0` | `net_clk2` | clk ↑ 전 Y 안정 |
| 574 setup | `net_d0` | `net_clk2` | D가 ↑ 전 ≥5 ns 안정 |
| MSB 마진 | `net_y7` | clk | SUB 벡터, MSB 안정 |

B3c 타이밍은 **hwsim OSC 없음** — 스코프 필수. 사전 마진:

```bash
python -m hwsim run hw/tests/alu_b3_latch.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
```

### 완료 기준 (B3c)

- [ ] SUB 벡터: **≥2 클록** 연속 Q 정확
- [ ] 2 MHz setup OK, 또는 기록된 저속 클록 (~1.7 MHz)

---

## 574 핀 참조 (B3b/B3c)

| Ref | Pin | Net |
|-----|-----|-----|
| `U_REG_574_ACC` | D0..D7 | `net_y0..7` |
| | Q0..Q7 | `net_q0..7` |
| | CP | `net_clk` (B3b) / `net_clk2` (B3c) |
| | OE | GND |

핀 번호: `python -m hwsim pinout 74HC574`

---

## hwsim ↔ 빵판

| hwsim | 빵판 |
|-------|------|
| `net_a*` 자극 | DIP |
| 제어 넷 | DIP / 치트시트 타이 |
| `net_clk2` @ 2 MHz | OSC + 74HC74 |
| Slack FAIL | 클록 낮추기 또는 SUB 캐리 배선 단축 |

타이밍 (max corner): SUB **151 ns**, logic **46 ns**, ADD **108 ns** (2 MHz Execute 반주기 **250 ns**). [alu-opcodes-timing.md](../alu-opcodes-timing.md) v1.3.

---

## 고장 분리

| 증상 | 조치 |
|------|------|
| Y 틀림 (B3a) | 치트시트 재확인; INC/DEC는 **153_B** (`b_const_sel`); 산술은 **157_YBP** |
| CP 후 Q≠Y | Setup 위반 — CP 에지 느리게 또는 Y 안정 후 펄스 |
| 2 MHz에서 Q 틀림 | 스코프 Y vs clk; 배선 단축 또는 클록 하향 |
| hwsim FAIL | `--report` 옵션; B3c는 스코프 |

netlist 변경 후 regen: [hw-sim.md](../simulation/hw-sim.md) § ALU regen chain.

---

## 다음 단계

→ [M2a-cpld-decode.md](M2a-cpld-decode.md)
