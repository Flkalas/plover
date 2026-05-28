# Plover 마이크로코드 명세 (시뮬레이터 v0.1)

버전: **0.1** — RTL·`microasm`·웹 UI의 단일 진실 소스.

## 16비트 제어 워드 레이아웃

SST39SF010A ×2 병렬: `rom_low[addr]` = CW[7:0], `rom_high[addr]` = CW[15:8].

```
CW[15:0] = { alu_sel[3:0], reg_ctl[3:0], bus_ctl[3:0], branch[3:0] }
```

| 비트 | 필드 | 설명 |
|------|------|------|
| 15:12 | `alu_sel` | ALU 연산 (아래 표) |
| 11:8 | `reg_ctl` | 레지스터 읽기/쓰기 |
| 7:4 | `bus_ctl` | 데이터 버스 라우팅 |
| 3:0 | `branch` | PC·플래그·분기 |

## ALU Select (`alu_sel`)

| 값 | 이름 | 동작 |
|----|------|------|
| 0 | NOP | 결과 = 0, 플래그 유지 |
| 1 | ADD | A + B |
| 2 | SUB | A + ~B + 1 (2의 보수) |
| 3 | AND | A & B |
| 4 | OR | A \| B |
| 5 | XOR | A ^ B |
| 6 | NOT | ~A (B 무시) |
| 7 | PASS_A | A |
| 8 | PASS_B | B |
| 9 | INC | A + 1 |
| 10 | DEC | A - 1 |
| 11 | CMP | SUB, 플래그만 갱신 (결과 버림) |
| 12–15 | — | 예약 (NOP 취급) |

- **A** 포트: `reg_ctl` 읽기로 선택된 레지스터.
- **B** 포트: `bus_ctl`이 REG→ALU_B일 때 선택 레지스터, 그 외 0.

플래그 (래치): **C** = carry out, **Z** = (결과 == 0). CMP/SUB/ADD 등 산술·논리 연산 후 `branch`에 따라 갱신.

## Register Control (`reg_ctl`)

| 비트 | 이름 | 설명 |
|------|------|------|
| 11:9 | `reg_idx` | 레지스터 0–6 (3비트) |
| 8 | `reg_we` | 0: `R[reg_idx]` → ALU A, 1: 버스 → `R[reg_idx]` 쓰기 |

레지스터 이름 (74HC574 ×7):

| idx | 이름 | 용도 (권장) |
|-----|------|-------------|
| 0 | R0 | 범용 / 메모리 주소 하위 |
| 1 | R1 | 범용 / 메모리 주소 상위 |
| 2 | R2 | 점프 타깃 / 범용 |
| 3 | R3 | 범용 |
| 4 | R4 | 범용 |
| 5 | R5 | ACC |
| 6 | R6 | TMP |

## Bus Control (`bus_ctl`)

| 값 | 이름 | 동작 |
|----|------|------|
| 0 | IDLE | 버스 갱신 없음 |
| 1 | ALU_TO_REG | ALU 결과 → 레지스터 쓰기 데이터 |
| 2 | REG_TO_ALU_B | `reg_idx` 레지스터 → ALU B |
| 3 | MEM_READ | 주소 = {R1,R0}, 읽기 → 버스 |
| 4 | MEM_WRITE | 주소 = {R1,R0}, 버스 → SRAM |
| 5 | IMM8_LO | CW 다음 주소 ROM[PC+1][7:0] → ALU B (2워드 명령) |
| 6–15 | — | 예약 |

메모리 주소 16비트: `addr = {R1, R0}` (시뮬 MVP).

## Branch / Misc (`branch`)

| 값 | 이름 | PC 동작 |
|----|------|---------|
| 0 | INC | PC ← PC + 1 |
| 1 | HOLD | PC 유지 |
| 2 | JMP | PC ← {R1, R0} |
| 3 | BEQ | Z==1이면 PC ← {R1, R0}, 아니면 PC+1 |
| 4 | BNE | Z==0이면 PC ← {R1, R0}, 아니면 PC+1 |
| 5 | HALT | 시뮬 정지 (`halted=1`) |
| 6 | INC2 | PC ← PC + 2 (IMM8_LO용) |
| 7–15 | — | INC와 동일 |

## 마이크로어셈블리 문법 (`microasm`)

```text
; 주석
@0000
alu ADD | reg R0<=R1 | bus REG_TO_ALU_B | branch INC
```

키워드는 대소문자 무시. 필드 구분자: `|`.

- `alu <OP>`
- `reg R<n><=R<m>` 또는 `reg R<n><=bus` / `reg R<n>=>alu` (읽기)
- `bus <NAME>`
- `branch <NAME>`

## ROM 이미지

- `rom_low.hex`, `rom_high.hex`: 한 줄당 바이트 1개 (Verilog `$readmemh`).
- `pack_rom.py`로 16비트 워드 목록 병합.

## 확장 (하드웨어 확정 후)

- 16비트 ADD/ADC: `lib/add16.micro` (2사이클).
- 8비트 곱셈: `lib/mul8.micro` (8–16사이클).
- MMIO (74HC138): `branch` 예약 필드 확장.
