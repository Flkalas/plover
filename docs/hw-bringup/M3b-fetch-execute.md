# M3b — Fetch path and macro execution (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M3b |
| **Goal** | DIP 없이 ROM에서 명령 fetch → CW 자동 → **첫 프로그램** HALT |
| **선행** | [M2b G6](M2b-gpr-datapath.md#g6), [M3a](M3a-control-store.md) |

---

## 1. 추가되는 블록

| 블록 | IC (권장) | 넷 | 역할 |
|------|-----------|-----|------|
| **PC** | 574×1~2 | `net_pc0..15` | instruction address |
| **IR/MBR** | 574 | `net_ir0..7` | fetched opcode byte |
| **Phase** | 74HC161 (하위 2bit) | `net_ph0..1` | micro-phase 0..2 |
| **CW addr mux** | 157/153 | Flash A0..5 | `{opcode,phase}` |
| **PC+1** | 283 (low) | — | sequential fetch |

> v0.1 breadboard: PC high byte는 DIP 프리셋 또는 2번째 574로 단순화 가능. **F0–F2는 low-page `$00xx` 만** 사용.

---

## 2. 주소 MUX 모드

| 모드 | MUX 선택 | A 버스 소스 |
|------|----------|-------------|
| **Instruction fetch** | `FETCH=1` | PC → ROM/RAM |
| **CW read** | `FETCH=0` | `$4000 \| ((opcode<<2)\|phase)` |
| **Data** | `MEM_RD/WR` | effective addr (LDA/STA operand) |

RESET 시: CPLD가 `$FFFC` → vector → PC load `$0000` (Boot).

---

## 3. 한 매크로 명령 타임라인 (@ 2 MHz)

```
[fetch opcode @ PC] → ph0 (CW) → ph1 (CW) → … → [PC += insn_size] → phase := 0
```

ADD (`0x01`, 2-byte header `01 imm`):

| 순서 | phase | CW @ | 동작 |
|------|-------|------|------|
| 1 | 0 | `$4004` | R0→A |
| 2 | 1 | `$4005` | R1→B |
| 3 | 2 | `$4006` | Y→R2 |

---

## 4. 단계별 실장 (F0–F6)

### F0 — RESET → PC

**작업:**

1. `MAP_MODE=0` (Boot).
2. `RESET_N` 버튼 눌렀다 뗌.
3. 로직프로브: 주소 MUX가 `$FFFC` → vector → **`$0000`** 근처.

**Pass:** RESET 해제 후 첫 fetch 주소 = ROM `$0000`.

---

### F1 — Instruction fetch

**작업:**

1. PC를 `$0000`에 로드 (RESET 또는 수동 프리셋).
2. `ROM_CS`, `/OE` 활성.
3. 클록 1 edge 또는 조합 읽기로 **IR** 래치.

**Pass:** IR = ROM `$0000` 바이트 (테스트 ROM 아래 참조).

**최소 테스트 ROM hex (`$0000`부터):**

```
02 42    ; LDA $42  (opcode 02, imm 0x42)
01 00    ; ADD $00  (R0+R1→R2; R1=0 가정)
0A       ; HALT
```

---

### F2 — CW 주소 생성

**작업:**

1. IR에서 opcode nibble = `0x02` (LDA).
2. phase = 0.
3. CW addr mux 출력 = `$4000 + (0x02<<2|0)` = **`$4008`**.

**Pass:** Flash read 데이터 = **`0x02`** (MEM_RD phase).

---

### F3 — CW → datapath

**작업:**

1. Flash D0–D7 → `alu8_decode` + `net_reg_we` + `y_oe` + `mem_rd`.
2. M2b G6와 **동일**한 LED/레지스터 동작 — CW 소스만 Flash.

**Pass:** LDA ph0에서 `MEM_RD`=1 관측; ph1에서 `REG_WE`=1.

---

### F4 — Phase 자동 순환

**작업:**

1. 74HC161 하위 2bit: 매 execute edge마다 ++.
2. 매크로 끝에서 phase sync reset (opcode decoder 또는 74 카운터 리셋).
3. ADD 3-phase 연속 — **opcode/phase DIP 제거**.

**Pass:** R0=`12`, R1=`34` → R2=`46` (ROM에 ADD 배치 또는 IR=01 트랩).

---

### F5 — PC advance

**작업:**

1. 2-byte insn 후 PC += 2 (283 low + carry TBD).
2. 다음 fetch가 `$0002` (위 테스트 ROM의 ADD).

**Pass:** 두 번째 IR = `0x01` (ADD).

---

### F6 — 전체 프로그램

**작업:**

1. §F1 hex를 NOR `$0000`에 병합 ([M3a](M3a-control-store.md) CW와 함께).
2. R1=0 초기화 (reset 또는 ROM에 MOV/LDA 추가).
3. `RESET` → `run` (free-running clk2).

**Pass:**

| 항목 | 기대 |
|------|------|
| HALT 도달 | PC @ HALT insn, clk 정지 또는 halt LED |
| R0 | `0x42` (LDA 결과 — calling conv 확인) |
| R2 | ADD 결과 (R1=0이면 `0x42`) |

**Sim 교차검증 (배선 전 필수):**

```bash
python -m plover_vm run hw/fixtures/sram/add_imm.sram.hex --engine micro --map run --max-steps 500
python -m pytest tests/test_engine_parity.py -q
```

---

## 5. 오실로스코프 (권장)

| CH-A | CH-B | Pass |
|------|------|------|
| Flash CW D0 | clk2 | CW 안정 후 edge |
| `net_reg_we` | clk2 | WE ↑ 전 CW 안정 |
| ROM `/OE` | PC stable | fetch setup |

---

## 6. M3b sign-off

- [ ] F0: RESET → `$0000` fetch path
- [ ] F2: LDA ph0 CW = `0x02` from `$4008`
- [ ] F4: ADD 3-phase 자동
- [ ] F6: §F1 ROM HALT + GPR 기대값
- [ ] Sim micro trace와 GPR 덤프 일치

---

## 7. 고장 분리

| 증상 | 확인 |
|------|------|
| CW=`00` | CW mux `{opcode,phase}`; Flash 주소선 |
| Phase 안 올라감 | 161 clock, macro complete reset |
| 잘못된 opcode | PC advance; endian; ROM merge |
| LDA 후 R0 틀림 | operand fetch 주소; MEM_RD 타이밍 |

---

## 8. 다음

→ [M4b-boot-hardware.md](M4b-boot-hardware.md)
