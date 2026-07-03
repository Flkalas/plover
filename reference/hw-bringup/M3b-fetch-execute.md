# M3b — Fetch path and macro execution (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M3b |
| **Goal** | ROM fetch → **CPLD FSM (idx5)** → operand via MBR → 첫 프로그램 HALT |
| **선행** | [M2b G5](M2b-gpr-datapath.md#g5--fsm-add-3-phase), [M3a](M3a-control-store.md) |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) §5–7 |

---

## 1. 추가되는 블록

| 블록 | IC | 넷 | 역할 |
|------|-----|-----|------|
| **PC** | 574+161 | `net_pc0..15` | instruction address |
| **IR** | 574 | `net_ir0..7` | opcode byte → CPLD `OPC[4:0]` |
| **MBR** | 574 | `net_mbr0..7` | operand imm8 / abs16 lo |
| **MBR hi** | 574 or PC+2 path | — | abs16 high byte (BEQ/JMP) |
| **Phase** | CPLD internal | `phase[1:0]` | micro-phase 0..2 |
| **FLG** | 574 | Z, C | BEQ @ macro_end |
| **PC+1** | 283 (low) | — | sequential fetch |

**없음:** PARAM 574, Flash `$4000` CW fetch, per-phase Flash addr mux.

---

## 2. 주소 MUX · 오퍼랜드 데이터 경로

| 모드 | `FETCH` | A 버스 소스 | 데이터 → |
|------|---------|-------------|----------|
| **Insn fetch** | 1 | PC → ROM/RAM | IR (byte0), MBR (byte1+) |
| **Data access** | 0 | MBR (or abs16 latch) | MEM_RD / MEM_WR |

### 오퍼랜드 취득 (Flash param 없음)

| 명령 | Fetch bytes | MBR / latch | FSM |
|------|-------------|-------------|-----|
| LDA `02 imm` | PC, PC+1 | imm8 → MBR | ph0 MEM_RD @ MBR |
| STA `03 imm` | PC, PC+1 | imm8 → MBR | ph1 MEM_WR @ MBR |
| LDIO/STIO | 2-byte | imm8 → MBR | MMIO decode on high nibble |
| BEQ/JMP | 3-byte | abs16 LE → MBR+hi | macro_end PC_LOAD_EN |
| ADD `01 imm` | PC, PC+1 | imm8 → R1 (ph0/1) | ALU_REG |
| TFR `14` | PC only | — | XFER 1 phase |

RESET: **74HC157** → `$FFFC` → PC `$0000` (Boot).

---

## 3. 분기 · 플래그 타이밍

| 단계 | 동작 |
|------|------|
| BEQ ph0 | ALU SUB (or prior CMP) → **FLG 574** ← Z |
| BEQ macro_end | CPLD `PC_LOAD_EN <= FLG_Z`; if Z, PC ← abs16 in MBR |
| JMP macro_end | `PC_LOAD_EN <= 1`; PC ← abs16 |
| Non-branch macro_end | `PC_LOAD_EN=0`; PC += insn_length (283/161 glue) |

**관측:** 스코프 on `FLG_Z`, `PC_LOAD_EN`, PC transition.

---

## 4. 매크로 타임라인 (@ 2 MHz)

```
[fetch opcode+operand] → FSM ph0..N (idx5) → [branch or PC+=len]
```

### ADD (`0x01`)

| phase | idx5 key | 동작 |
|-------|----------|------|
| 0 | `0x04` | R0→A; imm→R1 optional |
| 1 | `0x05` | R1→B |
| 2 | `0x06` | ADD → R2 |

### LDA (`0x02`)

| phase | 동작 |
|-------|------|
| 0 | FETCH=0; MEM_RD @ MBR |
| 1 | REG_WE → R0 |

### TFR20 (`0x14`, 1 byte)

| phase | 동작 |
|-------|------|
| 0 | R2 ← R0 (XFER; idx5 `0x50`) |

---

## 5. 단계별 실장 (F0–F5)

### F0 — RESET → PC

`MAP_MODE=0`, RESET → fetch `$FFFC` → **`$0000`**.

### F1 — Instruction fetch

**테스트 ROM (`$0000`):**

```
02 42    ; LDA $42
01 00    ; ADD $00
0A       ; HALT
```

**Pass:** IR = `0x02`; after 2nd fetch MBR = `0x42`.

### F2 — FSM → datapath

1. IR=`0x02` → FSM MEM_LD (idx5 decode `OPC=0x02`).
2. ph0: `FETCH=0`, `MEM_RD` @ MBR=`$42`.
3. ph1: `REG_WE` → R0.

### F3 — PC advance

LDA: PC += 2 after macro; phase reset.

### F4 — Full mini-program

LDA → ADD → HALT. **Pass:** HALT @ expected GPR (scope/LED).

### F5 — BEQ smoke (optional)

ROM: CMP + BEQ; verify `PC_LOAD_EN` only when Z=1.

---

## 6. M3b sign-off

- [ ] F0–F4 Pass on **breadboard** (not pre-flight sim)
- [ ] Operand path: MBR latched before MEM_RD
- [ ] No Flash param / `$4000` fetch in path
- [ ] BEQ: FLG_Z gates `PC_LOAD_EN`

---

## 7. 다음

→ [M4a-boot-sim.md](M4a-boot-sim.md) · [M4b-boot-hardware.md](M4b-boot-hardware.md)
