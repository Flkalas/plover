# ALU 명령어 · 조합 지연 (alu8)

**버전:** 1.0 · **기준일:** 2026-06-01  
**블록:** [`hw/netlist/blocks/alu8.yaml`](../hw/netlist/blocks/alu8.yaml) · **디코더:** [`alu8_decode.yaml`](../hw/netlist/blocks/alu8_decode.yaml)

12개 `alu_sel[3:0]` (제어 워드 `[15:12]`) 연산의 동작·제어·**조합 전파 지연**을 한 표로 정리합니다.  
지연 값은 hwsim [`74hc.yaml`](../hw/timing/74hc.yaml) **datasheet typ/max** 합산(배선 지연 0)이며, **2.0 MHz** 시스템의 Execute 반주기 예산 **250 ns** 대비 slack을 함께 기록합니다.

실기 치트시트: [`hw-bringup-b3-opcode.md`](hw-bringup-b3-opcode.md) · 마이크로코드 ISA: [`archive/verilog-sim/docs/microcode-spec.md`](../archive/verilog-sim/docs/microcode-spec.md)

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
| 11 | `0xB` | **CMP** | SUB와 동일, **결과 래치 없음** | C, Z만 갱신 |
| 12–15 | — | *(예약)* | NOP 취급 | — |

- **A** · **B**: `net_a0..7`, `net_b0..7` (CPU: ACC.Q → A 직결, B ← CPLD `q_b` 또는 SRAM).
- **INC/DEC**: `net_b0..7` 구동 금지 — `b_const_sel` + `b_const_bit1..7` 만 사용 ([bringup §INC/DEC](hw-bringup-b3-opcode.md)).

---

## 2. 제어 신호 (`alu_sel` → 하드와이어)

| sel | Op | sub | cin | b_sel | b_const_sel | s1:s0 | c3_sel | 283 B-side |
|-----|-----|-----|-----|-------|-------------|-------|--------|------------|
| 0 | NOP | 0 | 0 | 0 | 0 | 00 | 0 | 0 |
| 1 | ADD | 0 | 0 | 0 | 0 | 00 | 0 | B |
| 2 | SUB | 1 | 1 | 1 | 0 | 00 | 0 | ~B |
| 3 | AND | 0 | 0 | 0 | 0 | 01 | 0 | — |
| 4 | OR | 0 | 0 | 0 | 0 | 10 | 0 | — |
| 5 | XOR | 0 | 0 | 0 | 0 | 11 | 0 | — |
| 6 | NOT | 0 | 0 | 0 | 0 | 11 | 1 | — |
| 7 | PASS_A | 0 | 0 | 0 | 0 | 01 | 0 | B=0xFF |
| 8 | PASS_B | 0 | 0 | 0 | 0 | 01 | 0 | A=0xFF |
| 9 | INC | 0 | 0 | 0 | **1** | 00 | 0 | `0x01` via B2 |
| 10 | DEC | 0 | 0 | 0 | **1** | 00 | 0 | `0xFF` via B2 |
| 11 | CMP | 1 | 1 | 1 | 0 | 00 | 0 | ~B |

출력 MUX: `s1:s0` = 00 sum · 01 AND · 10 OR · 11 C3(XOR 또는 ~A).

---

## 3. 조합 전파 지연 (operand → Y)

예산: **250 ns** = 2.0 MHz Execute 반주기 ([`microarch-throughput.md`](microarch-throughput.md) §4).

### 3.1 opcode별 지연 · slack

| sel | Op | 경로 등급 | typ (ns) | max (ns) | slack @ max (ns) | 비고 |
|-----|-----|-----------|----------|----------|------------------|------|
| 0 | NOP | — | — | — | — | 출력 0, 타이밍 무관 |
| 1 | ADD | adder | 107 | **118** | 132 | 283 ripple → 153 sum |
| 2 | SUB | **critical** | 138 | **169** | **81** | **시스템 worst-case** |
| 3 | AND | logic | 26 | 43 | 207 | 08 → 153 |
| 4 | OR | logic | 26 | 43 | 207 | 32 → 153 |
| 5 | XOR | xor | 37 | 61 | 189 | 86 → 157 OUT → 153 |
| 6 | NOT | xor | 37 | 61 | 189 | 04 → 157 OUT → 153 |
| 7 | PASS_A | logic | 26 | 43 | 207 | AND + 마스크 |
| 8 | PASS_B | logic | 26 | 43 | 207 | AND + 마스크 |
| 9 | INC | adder | 107 | 118 | 132 | A + B2 상수; B2 선택 시 max **136** |
| 10 | DEC | adder | 107 | 118 | 132 | INC와 동일 경로 |
| 11 | CMP | **critical** | 138 | **169** | **81** | SUB와 동일 datapath |

**worst-case:** **SUB / CMP — 169 ns @ max** (slack **81 ns**).  
**fastest (유효 연산):** AND / OR / PASS — **43 ns @ max**.

### 3.2 canonical critical path (bit0, @ max)

| Op | ref.pin hop chain |
|----|-------------------|
| **SUB / CMP** | `86_INV_0.A` → `Y` → `157_B_0.1B` → `1Y` → `157_B2_0.1A` → `1Y` → `283_LO.B0` → `C4` → `283_HI.C4` → `153_0.1C0` → `1Y` |
| **ADD / INC / DEC** | `283_LO.A0` → `C4` → `283_HI.C4` → `153_0.1Y` (INC/DEC: B2 cascade 추가 시 +18 ns) |
| **XOR** | `86_XOR_0.A` → `Y` → `157_OUT_0.4A` → `4Y` → `153_0.1C3` → `1Y` |
| **AND / PASS** | `08_0.A` → `Y` → `153_0.1C1` → `1Y` |

### 3.3 ACC 래치 (Y → 574.Q)

B3c 브링업 경로 — ALU 출력이 **다음 posedge** 전에 setup 만족해야 함.

| 구간 | typ (ns) | max (ns) | slack @ max (ns) |
|------|----------|----------|------------------|
| `153_0.1Y` → `574_ACC.D0` (+ setup) | 17 | 28 | 222 |

전체 **operand → ACC.Q** (max): SUB 기준 **169 + 23 (574 t_pd)** ≈ **192 ns** (ACC.Q 직결 A-side, CPLD async read 미포함).

### 3.4 CW 디코드 오버헤드 (v0.1 E2E)

v0.1 CPU는 **8-bit CW** (Flash B7–B4 = `ALU_OP`, B3 = `REG_WE`) + **574×4 GPR** + **ATF1504AS system CPLD** (`Reg_Sel`/`LOAD_R*` comb decode)로 구성된다. ALU comb 경로는 v1과 동일하며, E2E budget에 CPLD `t_pd` (~15 ns max)와 574 dual-read (`t_pd_q` ~23 ns)만 **직렬 가산**한다.

| 구간 | typ (ns) | max (ns) | 비고 |
|------|----------|----------|------|
| Flash CW → `ALU_OP` | — | — | 병렬 8b; execute 위상 addr mux |
| `ALU_OP` → SUB Y | 169 | 169 | [`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml) |
| CPLD `Reg_Sel` → 574 QA/QB | 10 | 15 | [`cpld.yaml`](../hw/timing/cpld.yaml) |
| SUB Y → 574 latch setup | 17 | 28 | §3.3 |

[`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml): `net_alu_op0` → SUB datapath **169 ns @ max** — 08/04/32 comb 디코더 hop은 SUB critical path와 **동일** (추가 ALU hop 없음). v2 regression: [`v2_regfile_574`](../hw/tests/regfile_574.yaml).

---

## 4. hwsim 검증 · 파형 측정

| 테스트 | 검증 opcode / 구간 | 리포트 delay (max) |
|--------|-------------------|-------------------|
| [`alu8_full`](../hw/tests/alu8_full.yaml) | 12 opcode 기능 | — |
| [`alu8_timing`](../hw/tests/alu8_timing.yaml) | ADD carry · AND | ADD **118** ns, AND hop **15** ns |
| [`alu_b3_sub_critical`](../hw/tests/alu_b3_sub_critical.yaml) | SUB | **169** ns; wave `sub_en→y0` **76** ns |
| [`alu_b3_xor_critical`](../hw/tests/alu_b3_xor_critical.yaml) | XOR | **61** ns; wave `153_s0→y0` **28** ns |
| [`alu_b3_latch`](../hw/tests/alu_b3_latch.yaml) | ACC setup | **51** ns (153→574 CP) |
| [`alu_decode_timing`](../hw/tests/alu_decode_timing.yaml) | CW→SUB | **169** ns |
| [`alu283_carry`](../hw/tests/alu283_carry.yaml) | 283 only | ripple **90** ns |

```bash
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/alu8_timing.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
```

아티팩트: `build/hwsim/<test>/timing_report.json`

---

## 5. CPU 맥락 — 명령 “지연” (macro-cycle)

ALU 블록 자체는 **순수 조합**입니다. ISA 수준 지연은 FSM phase에 따릅니다.

| 계층 | 지연 | 설명 |
|------|------|------|
| ALU comb | **≤ 169 ns** | 위 §3 — Execute 반주기 250 ns **내** |
| Execute phase | **1 macro-half** (250 ns) | Flash CW + regfile + ALU + ACC latch |
| ALU-only µop (예: `ADD TMP`) | **1 Execute** | fetch 없음 — [microcode-spec-v1.2](microcode-spec-v1.2.md) §3.1 |
| Fetch+Execute 명령 (Phase Collapsing) | **2 macro-cycle** (1.0 µs) | T1 fetch + T3 exec — [microarch-throughput](microarch-throughput.md) §3.5 |
| 시스템 클록 | **2.0 MHz** | 500 ns macro-cycle, **250 ns** φ_fetch / φ_exec |

CPU E2E (Flash 70 ns + CPLD read 10–15 ns + ALU)는 별도 `cpu_v1_*` / `cpld_regfile_dual_read` 게이트에서 측정 — ALU 기여분 상한은 **169 ns @ max**.

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
| 2026-06-01 | 12 opcode · 제어 · typ/max 지연 · hwsim 교차표 초판 |
