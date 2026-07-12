# M3b — Fetch path and macro execution (v1.0 P12)

| Field | Value |
|-------|-------|
| **Milestone** | M3b |
| **Goal** | ROM/PROG fetch → **pipe CU** → operand via MBR → 첫 프로그램 HALT |
| **선행** | [M2b G4](M2b-gpr-datapath.md#g4--fsm-add-ph2), [M3a](M3a-control-store.md) |
| **Normative** | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) |

---

## 1. 추가되는 블록

| 블록 | IC | 넷 | 역할 |
|------|-----|-----|------|
| **PC** | 574+161 | `net_pc0..15` | instruction address |
| **IR** | 574 | `net_ir0..7` | opcode byte → CPLD `OPC[4:0]` |
| **MBR** | 574 | `net_mbr0..7` | operand imm8 / abs16 lo; **ALU B** |
| **MBR hi** | 574 or PC+2 path | — | abs16 high byte (BEQ/JMP/CALL) |
| **Pipe CU** | CPLD-CU | IF\|EX states | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) |
| **FLG** | 574 | Z, C | BEQ / flags |
| **PC+1** | 283 (low) | — | sequential fetch |

**없음:** PARAM 574, Flash `$4000` CW fetch, CPLD `q_b`, TFR comb.

---

## 2. 주소 MUX · 오퍼랜드 데이터 경로

| 모드 | `FETCH` / PROG | A 버스 소스 | 데이터 → |
|------|----------------|-------------|----------|
| **Insn fetch (IF)** | PROG | PC → Flash | IR (byte0), MBR (byte1+) |
| **Data access (EX)** | DATA | MBR (or abs16 latch) | MEM_RD / MEM_WR |

### 오퍼랜드 취득

| 명령 | Fetch bytes | MBR / latch | Pipe intent |
|------|-------------|-------------|-------------|
| LDA `02 imm` | PC, PC+1 | imm8 → MBR (address) | MEM_STALL + REG_WE |
| STA `03 imm` | PC, PC+1 | imm8 → MBR | MEM_STALL + MEM_WR |
| LDIO/STIO | 2-byte | imm8 → MBR | MMIO + MEM_STALL |
| BEQ/JMP/CALL | 3-byte | abs16 LE → MBR+hi | BRANCH_BUBBLE / STACK_EX |
| RET | 1-byte | — | STACK_EX + PC_LOAD_EN |
| ADD `01 imm` | PC, PC+1 | imm8 → **MBR (held → ALU B)** | packed EX → **R0** |
| `0x10–0x1F` | — | — | **trap / invalid** |

### MBR hold (ALU EX)

During ADD/CMP EX: **do not reload MBR** — operand imm8 must remain on `net_mbr` for ALU B.

RESET: **74HC157** → `$FFFC` → PC `$0000` (Boot).

---

## 3. 분기 · 플래그 타이밍

| 단계 | 동작 |
|------|------|
| BEQ EX | ALU SUB (or prior CMP) → **FLG 574** ← Z |
| BEQ taken | CPLD `PC_LOAD_EN <= FLG_Z`; **BRANCH_BUBBLE**; PC ← abs16 |
| JMP | `PC_LOAD_EN`; **BRANCH_BUBBLE**; PC ← abs16 |
| CALL | **STACK_EX** push return PC; `PC_LOAD_EN`; PC ← abs16 |
| RET | **STACK_EX** pop → **PC_in**; `PC_LOAD_EN` |
| Non-branch retire | `PC_LOAD_EN=0`; PC advances with IF stream |

**관측:** 스코프 on `FLG_Z`, `PC_LOAD_EN`, PC transition.

---

## 4. 매크로 타임라인 (@ 2 MHz)

Active SYS tax: [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §4. Do **not** verify idle padding phases.

### ADD (`0x01`)

| Intent | 동작 |
|--------|------|
| IF | Fetch opcode / imm on PROG (imm may shadow prior EX) |
| EX | R0←R0+imm; `Y_OE`; `REG_WE`→R0; FLG_WE; **MBR hold** |

Typical SYS: **2** (stream → **1**).

### CMP (`0x0D`)

| Intent | 동작 |
|--------|------|
| IF | Fetch opcode / imm |
| EX | FLG_WE only; B from MBR |

### CALL (`0x06`)

| Intent | 동작 |
|--------|------|
| IF | Abs16 |
| EX | **STACK_EX** push; `PC_LOAD_EN`; bubble as needed |

### RET (`0x07`)

| Intent | 동작 |
|--------|------|
| EX | **STACK_EX** pop → **PC_in**; `PC_LOAD_EN`; bubble |

Return stack semantics: [microcode-spec.md](../hardware/microcode-spec.md) §2.3.

### LDA (`0x02`)

| Intent | 동작 |
|--------|------|
| EX | MEM_RD @ MBR; REG_WE → R0; **MEM_STALL** |

---

## 5. 단계별 실장 (F0–F5)

### F0 — RESET → PC

`MAP_MODE=0`, RESET → fetch `$FFFC` → **`$0000`**.

### F1 — Instruction fetch

**테스트 ROM (`$0000`):**

```hex
02 42    ; LDA $42
01 00    ; ADD $00  → R0 = mem[$42] + 0
0A       ; HALT
```

**Pass:** IR = `0x02`; after 2nd fetch MBR = `0x42`.

### F2 — Pipe CU → datapath

1. IR=`0x02` → MEM load path.
2. EX: `MEM_RD` @ MBR=`$42` (**MEM_STALL** as needed).
3. `REG_WE` → R0.

### F3 — PC advance

LDA: PC advances with IF stream after retire.

### F4 — Full mini-program

LDA → ADD → HALT. **Pass:** R0 holds final sum.

### F5 — BEQ smoke (optional)

ROM: CMP + BEQ; verify `PC_LOAD_EN` only when Z=1; taken → **BRANCH_BUBBLE**.

---

## 6. M3b sign-off

- [ ] F0–F4 Pass on **breadboard**
- [ ] Align with [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) SYS sheet (no idle padding)
- [ ] MBR hold during ADD/CMP EX
- [ ] No Flash param / `$4000` fetch in path
- [ ] BEQ: FLG_Z gates `PC_LOAD_EN`

---

## 7. 다음

→ [M4a-boot-sim.md](M4a-boot-sim.md) · [M4b-boot-hardware.md](M4b-boot-hardware.md)

---

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Retarget timelines to pipe CU |
| 2026-07-07 | CALL/RET — 3B/1B fetch; stack push/pop |
| 2026-07-07 | MBR→B; ADD→R0; TFR removed |

