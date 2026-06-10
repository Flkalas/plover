# M3a — Control store pack and NOR programming (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M3a |
| **Goal** | `cw.hex` 생성·검증·NOR `$4000` 소각 |
| **Normative** | [microcode-spec.md](../microcode-spec.md) · [rom-architecture.md](../rom-architecture.md) |

---

## 1. 개념 (작업자용)

CPU는 매크로 opcode마다 **1~3 micro-phase** 를 실행합니다. 각 phase마다 Flash `$4000` 대역에서 **10비트 CW (2바이트)** 를 읽습니다.

```
index = (opcode[3:0] << 2) | phase[1:0]
Flash_lo = $4000 + 2*index      → 574 CW_L
Flash_hi = $4000 + 2*index + 1  → 574 CW_H (REG_SEL[1:0])
```

| CW bit | 신호 | Latch |
|--------|------|-------|
| B9–B8 | REG_SEL | CW_H → CPLD |
| B7–B4 | ALU_OP | CW_L |
| B3 | REG_WE | CW_L |
| B2 | Y_OE | CW_L |
| B1 | MEM_RD | CW_L |
| B0 | MEM_WR | CW_L |

---

## 2. 소프트웨어 절차 (배선 없이 가능)

### 2.1 빌드

```bash
cd D:\Github\plover   # 리포 루트
python tools/pack_control_store.py --build-fixtures
```

생성 파일:

| 파일 | 내용 |
|------|------|
| `hw/fixtures/control/cw.hex` | 4096바이트 (2048 슬롯 × 2) |
| `hw/fixtures/control/nor_cw_region.hex` | Flash `$4000` 오프셋 포함 슬라이스 |

### 2.2 검증

```bash
python tools/verify_control_store.py
python -m pytest tests/test_engine_parity.py -q
```

**Pass:** verify 스크립트 exit 0; parity 테스트 green.

---

## 3. Readback 스팟 체크 표 (소각 후)

프로그래머로 Flash 읽기 — 아래 주소의 **바이트**가 일치해야 함:

| Flash addr | Idx | Opcode·Ph | CW (hex) | 의미 |
|------------|-----|-----------|----------|------|
| `$4004` | 4 | ADD ph0 | `14` | R0→A, Y_OE |
| `$4005` | 5 | ADD ph1 | `14` | R1→B |
| `$4006` | 6 | ADD ph2 | `1C` | REG_WE, Y→R2 |
| `$4008` | 8 | LDA ph0 | `02` | MEM_RD |
| `$4009` | 9 | LDA ph1 | `08` | REG_WE |
| `$4014` | 20 | JMP ph0 | `00` | macro only |
| `$4034` | 52 | CMP ph0 | `B0` | CMP, Y_OE=0 |

전체: [microcode-spec.md](../microcode-spec.md) §3.

---

## 4. NOR 소각 절차

### 4.1 선행

- [M2b-memory.md](M2b-memory.md) — SST39 소켓 배선 완료
- 병렬 Flash 프로그래머 (SST39SF010 호환)

### 4.2 이미지 병합

| 영역 | 소스 | Flash offset |
|------|------|--------------|
| CW only (M3a) | `cw.hex` 또는 `nor_cw_region.hex` | `$4000` |
| Boot (M4b) | `boot_rom.hex` | `$0000` |
| Vector | `boot_vector.hex` | CPU `$FFFC` 이미지 |

**M3a만:** CW 영역만 굽기 — **boot 영역 덮어쓰지 않기**.

### 4.3 소각 후 벤치 (fetch 없이)

1. 주소 DIP/카운터로 `$4004` 선택.
2. `/OE` 활성, D0–D7을 **LED 8개**에 연결.
3. 기대: LED 패턴 = `0x14` = `0001_0100`.

`alu8_decode` 블록이 있으면 CW → ALU 제어선으로 직결해 ADD ph0 관측 ([M2b G6](M2b-gpr-datapath.md#g6--수동-cw--2-mhz-add-3-phase)).

---

## 5. 수동 CW DIP 표 (M2b G6 / 디버그용)

8비트 DIP: B7(왼쪽) … B0(오른쪽).

| Ph | CW | B7-4 ALU | B3 WE | B2 Y_OE | B1 RD | B0 WR |
|----|-----|----------|-------|---------|-------|-------|
| ADD 0 | 14 | ADD(1) | 0 | 1 | 0 | 0 |
| ADD 1 | 14 | ADD(1) | 0 | 1 | 0 | 0 |
| ADD 2 | 1C | ADD(1) | 1 | 1 | 0 | 0 |
| LDA 0 | 02 | NOP(0) | 0 | 0 | 1 | 0 |
| LDA 1 | 08 | NOP(0) | 1 | 0 | 0 | 0 |

ALU_OP 열거: [microcode-spec.md](../microcode-spec.md) §4.

---

## 6. M3a sign-off

- [ ] `pack_control_store.py --build-fixtures` OK
- [ ] `verify_control_store.py` OK
- [ ] `test_engine_parity.py` OK
- [ ] NOR readback §3 표 일치 (최소 ADD+LDA 5주소)
- [ ] 소각 명령·프로그래머 설정 lab notebook 기록

---

## 7. 다음

→ [M3b-fetch-execute.md](M3b-fetch-execute.md)
