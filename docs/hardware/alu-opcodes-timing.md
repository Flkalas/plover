# ALU 명령어 · 조합 지연 (alu8)

**버전:** 1.3 · **기준일:** 2026-06-02 (Phase B2 Gigatron logic + B1 arith)  
**블록:** [`hw/netlist/blocks/alu8.yaml`](../hw/netlist/blocks/alu8.yaml) · **디코더:** [`alu8_decode.yaml`](../hw/netlist/blocks/alu8_decode.yaml)

12개 `alu_sel[3:0]` (제어 워드 `[15:12]`) 연산의 동작·제어·**조합 전파 지연**을 한 표로 정리합니다.  
지연 값은 hwsim [`74hc.yaml`](../hw/timing/74hc.yaml) **datasheet typ/max** 합산(배선 지연 0)이며, **2.0 MHz** 시스템의 Execute 반주기 예산 **250 ns** 대비 slack을 함께 기록합니다.

실기 치트시트: [`b3-opcode.md`](../hw-bringup/b3-opcode.md) · 마이크로코드 ISA: [`archive/verilog-sim/docs/microcode-spec.md`](../archive/verilog-sim/docs/microcode-spec.md)

---

## 1. 명령어 요약

| sel | `alu_op` | Mnemonic | 동작 | C / Z 플래그 |
|-----|----------|----------|------|---------------|
| 0 | `0x0` | **NOP** | Y = 0 (산술·논리 무효) | 유지 |
| 1 | `0x1` | **ADD** | Y = A + B | C = carry, Z = (Y==0) |
| 2 | `0x2` | **SUB** | Y = A + ~B + 1 (2의 보수) | C = carry, Z; borrow = ~C_hi |
| 3 | `0x3` | **AND** | Y = A & B | Z |
| 4 | `0x4` | **OR** | Y = A \| B | Z |
| 5 | `0x5` | **XOR** | Y = A ^ B | Z |
| 6 | `0x6` | **NOT** | Y = ~A (B 무시) | Z |
| 7 | `0x7` | **PASS_A** | Y = A (`AND` + B=0xFF) | Z |
| 8 | `0x8` | **PASS_B** | Y = B (`AND` + A=0xFF) | Z |
| 9 | `0x9` | **INC** | Y = A + 1 (B2 상수 `0x01`) | C, Z |
| 10 | `0xA` | **DEC** | Y = A − 1 (B2 상수 `0xFF`) | C, Z |
| 11 | `0xB` | **CMP** | SUB와 동일 Y | C, Z — `net_cmp_z`=`Y==0`, `net_cmp_c_ge`=`net_c_hi` |
| 12–15 | — | *(예약)* | NOP 취급 | — |

- **A** · **B**: `net_a0..7`, `net_b0..7` (CPU: ACC.Q → A 직결, B ← CPLD `q_b` 또는 SRAM).
- **INC/DEC**: `net_b0..7` 구동 금지 — `153_B` MUX: INC=`b_const_sel=1,b_sel=0`; DEC=`b_const_sel=1,b_sel=1` ([bringup §INC/DEC](../hw-bringup/b3-opcode.md)).

---

## 2. 제어 신호 (`alu_sel` → 하드와이어)

| sel | Op | cin | b_sel | b_const_sel | s1:s0 | lgc3:0 | 153_B (sel) |
|-----|-----|-----|-------|-------------|-------|--------|-------------|
| 0 | NOP | 0 | 0 | 0 | 00 | 0000 | 0 — B |
| 1 | ADD | 0 | 0 | 0 | 00 | 0000 | 0 — B |
| 2 | SUB | 1 | 1 | 0 | 00 | 0000 | 1 — ~B |
| 3 | AND | 0 | 0 | 0 | 01 | 0001 | — |
| 4 | OR | 0 | 0 | 0 | 10 | 0111 | — |
| 5 | XOR | 0 | 0 | 0 | 11 | 0110 | — |
| 6 | NOT | 0 | 0 | 0 | 11 | 1000 | — |
| 7 | PASS_A | 0 | 0 | 0 | 01 | 0001 | B=FF mask |
| 8 | PASS_B | 0 | 0 | 0 | 01 | 0001 | A=FF mask |
| 9 | INC | 0 | 0 | **1** | 00 | 0000 | 2 — `0x01` |
| 10 | DEC | 0 | **1** | **1** | 00 | 0000 | 3 — `0xFF` |
| 11 | CMP | 1 | 1 | 0 | 00 | 0000 | 1 — ~B |

`lgc3:0` → `net_lgc3..0` (153_L C inputs). Logic ops: `s0|s1` → **157_YBP** selects `net_y_logic`.

---

## 3. 조합 전파 지연 (operand → Y)

예산: **250 ns** = 2.0 MHz Execute 반주기 ([`microarch-throughput.md`](microarch-throughput.md) §4).

### 3.1 opcode별 지연 · slack

| sel | Op | 경로 등급 | max (ns) | slack @ max (ns) | 비고 |
|-----|-----|-----------|----------|------------------|------|
| 0 | NOP | adder | **108** | 142 | sum path (Y=0) |
| 1 | ADD | adder | **108** | 142 | 283 → **157_YBP** |
| 2 | SUB | **critical** | **151** | **99** | **시스템 worst-case** (B1 유지) |
| 3 | AND | logic | **46** | 204 | `153_L` → 157_YBP |
| 4 | OR | logic | **46** | 204 | |
| 5 | XOR | logic | **46** | 204 | |
| 6 | NOT | logic | **46** | 204 | |
| 7 | PASS_A | logic | **46** | 204 | AND pattern + B=FF |
| 8 | PASS_B | logic | **46** | 204 | AND pattern + A=FF |
| 9 | INC | adder | **108** | 142 | `153_B` → `0x01` |
| 10 | DEC | adder | **151** | **99** | `153_B` → `0xFF` (~B path) |
| 11 | CMP | **critical** | **151** | **99** | Y = SUB; flags §3.5 |

측정: [`alu8_opcode_timing`](../hw/tests/alu8_opcode_timing.yaml) · `build/hwsim/alu8_opcode_timing/timing_report.json` (@ **max**).

**worst-case (Y):** **SUB / CMP / DEC** — **151 ns** (slack **99 ns** @ 250 ns Execute half-period).  
**fastest:** logic opcodes — **46 ns**.

**Comb-limited Fmax (SUB 기준):** \(F \approx 1 / (2 \times 151\,\text{ns}) \approx 3.3\,\text{MHz}\) (574 setup·CPLD·Flash 별도). 명목 **2 MHz:** slack = 250 − 151 = **99 ns**.

### 3.2 canonical critical path (bit0, @ max)

| Op | ref.pin hop chain |
|----|-------------------|
| **SUB / CMP / DEC** | `net_b0` → `04_BINV_0` → `153_B_0.1C1` → `1Y` → `283_LO.B0` → `C4` → `283_HI.C4` → `157_YBP_0.1A` → `1Y` |
| **ADD / INC / NOP** | `283_LO.A0` → `C4` → `283_HI.C4` → `157_YBP_0.1A` → `1Y` |
| **AND / OR / XOR / NOT / PASS** | `153_L_0.A` → `Y` → `157_YBP_0.4B` → `4Y` |

### 3.3 ACC 래치 (Y → 574.Q)

B3c 브링업 경로 — ALU 출력이 **다음 posedge** 전에 setup 만족해야 함.

| 구간 | typ (ns) | max (ns) | slack @ max (ns) |
|------|----------|----------|------------------|
| `157_YBP_0.1Y` → `574_ACC.D0` (+ setup) | 17 | 28 | 222 |

전체 **operand → ACC.Q** (max): SUB 기준 **151 + 23 (574 t_pd)** ≈ **174 ns** (ACC.Q 직결 A-side, CPLD async read 미포함).

### 3.5 CMP 플래그 (SUB 유도, no 7485)

`ALU_CMP_SUB`: CMP/SUB 시 (`b_sel=1`, `cin=1`) **Z** = all `net_y==0`, **C_GE** = `net_c_hi`.  
hwsim [`alu8_cmp_sub`](../hw/tests/alu8_cmp_sub.yaml) — 플래그는 Y 경로와 **동일 오더**:

| 구간 | typ (ns) | max (ns) | 비고 |
|------|----------|----------|------|
| `net_b0` → `net_cmp_z` | — | **151** | SUB/CMP critical path |
| `net_b0` → `net_cmp_c_ge` | — | **151** | via `net_c_hi` @ 283 |

실기: `net_cmp_z` / `net_cmp_c_ge` → FLG 574 또는 CPLD; Execute 말 샘플 ([`alu8.md`](../hw/netlist/blocks/alu8.md)).

### 3.4 CW 디코드 오버헤드 (v1.0 E2E)

v1.0 CPU는 **10-bit CW** (B9–B8 `REG_SEL` in Flash hi byte; B7–B0 bus/ALU in lo) + **CPLD GPR** (`q_a`/`q_b` ~10 ns typ async read)로 구성된다. ALU comb 경로는 동일하며, E2E budget에 CPLD read path만 **직렬 가산**한다.

| 구간 | typ (ns) | max (ns) | 비고 |
|------|----------|----------|------|
| Flash CW → `ALU_OP` | — | — | 병렬 8b; execute 위상 addr mux |
| `ALU_OP` → SUB Y | 151 | 151 | [`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml) |
| CPLD `Reg_Sel` → 574 QA/QB | 10 | 15 | [`cpld.yaml`](../hw/timing/cpld.yaml) |
| SUB Y → 574 latch setup | 17 | 28 | §3.3 |

[`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml): `net_alu_op0` → SUB datapath **151 ns @ max** (B1 arith path; unchanged in B2). v2 regression: [`v2_regfile_574`](../hw/tests/regfile_574.yaml).

---

## 4. hwsim 검증 · 파형 측정

| 테스트 | 검증 opcode / 구간 | 리포트 delay (max) |
|--------|-------------------|-------------------|
| [`alu8_full`](../hw/tests/alu8_full.yaml) | 12 opcode 기능 | — |
| [`alu8_opcode_timing`](../hw/tests/alu8_opcode_timing.yaml) | 12 opcode slack | SUB **151** ns, logic **46** ns, ADD **108** ns |
| [`alu8_timing`](../hw/tests/alu8_timing.yaml) | ADD carry · logic hop | ADD **108** ns, `153_L` **46** ns |
| [`alu8_cmp_sub`](../hw/tests/alu8_cmp_sub.yaml) | CMP flags | `cmp_z` / `cmp_c_ge` **151** ns @ max |
| [`alu_b3_sub_critical`](../hw/tests/alu_b3_sub_critical.yaml) | SUB | **151** ns @ max; slack **99** ns |
| [`alu_b3_xor_critical`](../hw/tests/alu_b3_xor_critical.yaml) | XOR | **46** ns (`153_L` → 157_YBP) |
| [`alu_b3_latch`](../hw/tests/alu_b3_latch.yaml) | ACC setup | **51** ns (153→574 CP) |
| [`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml) | CW→SUB | **151** ns |
| [`alu283_carry`](../hw/tests/alu283_carry.yaml) | 283 only | ripple **90** ns |

```bash
python tools/gen_alu8_opcode_timing.py
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/alu8_opcode_timing.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
```

아티팩트: `build/hwsim/<test>/timing_report.json`

---

## 5. CPU 맥락 — 명령 “지연” (macro-cycle)

ALU 블록 자체는 **순수 조합**입니다. ISA 수준 지연은 FSM phase에 따릅니다.

| 계층 | 지연 | 설명 |
|------|------|------|
| ALU comb | **≤ 151 ns** | 위 §3 — Execute 반주기 250 ns **내** |
| Execute phase | **1 macro-half** (250 ns) | Flash CW + regfile + ALU + ACC latch |
| ALU-only µop (예: `ADD TMP`) | **1 Execute** | fetch 없음 — [microcode-spec-v1.2](microcode-spec-v1.2.md) §3.1 |
| Fetch+Execute 명령 (Phase Collapsing) | **2 macro-cycle** (1.0 µs) | T1 fetch + T3 exec — [microarch-throughput](microarch-throughput.md) §3.5 |
| 시스템 클록 | **2.0 MHz** | 500 ns macro-cycle, **250 ns** φ_fetch / φ_exec |

CPU E2E (Flash 70 ns + CPLD read 10–15 ns + ALU)는 별도 `cpu_v1_*` / `cpld_regfile_dual_read` 게이트에서 측정 — ALU 기여분 상한은 **151 ns @ max** (SUB; B2 logic **46 ns**).

---

## 6. 스모크 벡터

| Op | A | B | Y |
|----|---|---|---|
| SUB | `0x12` | `0x34` | `0xDE` |
| XOR | `0x12` | `0x34` | `0x26` |
| INC | `0x12` | — | `0x13` |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-02 | Phase B2: Gigatron `153_L`, **16** IC, opcode timing matrix, logic **46 ns** |
| 2026-06-02 | Phase B1: SUB **151 ns** max (`157_B2` 제거, `157_YBP` sum bypass) |
| 2026-06-02 | Phase A: SUB 179 ns max, `7485` CMP flags §3.5, 제어표 `sub` 제거 |
| 2026-06-01 | 12 opcode · 제어 · typ/max 지연 · hwsim 교차표 초판 |
