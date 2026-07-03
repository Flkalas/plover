# ALU 명령어 · 조합 지연 (alu8)

**버전:** 1.4 · **기준일:** 2026-07-04  
**블록:** [`hw/netlist/blocks/alu8.yaml`](../../hw/netlist/blocks/alu8.yaml)  
**디코드:** **M1** — [`alu8_decode.yaml`](../../hw/netlist/blocks/alu8_decode.yaml) 또는 [b3-opcode.md](../hw-bringup/b3-opcode.md) DIP · **SoC** — CPLD idx5 FSM ([control-and-decode.md](control-and-decode.md))

12개 `alu_sel[3:0]` 연산의 동작·제어·**조합 전파 지연**을 한 표로 정리합니다.  
지연 값은 pre-flight sim [`74hc.yaml`](../../hw/timing/74hc.yaml) **datasheet typ/max** 합산(배선 지연 0)이며, **2.0 MHz** Execute 반주기 **250 ns** 대비 slack을 함께 기록합니다.

실기 치트시트: [`b3-opcode.md`](../hw-bringup/b3-opcode.md) · ISA×phase: [`microcode-spec.md`](microcode-spec.md)

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
| 9 | `0x9` | **INC** | Y = A + 1 (`cin=1`, `bctrl=0000` → A+0+1) | C, Z |
| 10 | `0xA` | **DEC** | Y = A − 1 (`bctrl=1111`) | C, Z |
| 11 | `0xB` | **CMP** | SUB와 동일 Y | C, Z — `net_cmp_z`=`Y==0`, `net_cmp_c_ge`=`net_c_hi` |
| 12–15 | — | *(예약)* | NOP 취급 | — |

- **A** · **B**: `net_a0..7`, `net_b0..7`.
- **INC/DEC**: `net_b0..7` 구동 금지 — INC=`cin=1` + `bctrl=0000`; DEC=`bctrl=1111` ([bringup §INC/DEC](../hw-bringup/b3-opcode.md)).

---

## 2. 제어 신호 (`alu_sel` → 하드와이어)

| sel | Op | cin | bctrl3:0 | s1:s0 | lgc3:0 |
|-----|-----|-----|----------|-------|--------|
| 0 | NOP | 0 | 0000 | 00 | 0000 |
| 1 | ADD | 0 | 1100 | 00 | 0000 |
| 2 | SUB | 1 | 0011 | 00 | 0000 |
| 3 | AND | 0 | 0000 | 01 | 0001 |
| 4 | OR | 0 | 0000 | 10 | 0111 |
| 5 | XOR | 0 | 0000 | 11 | 0110 |
| 6 | NOT | 0 | 0000 | 11 | 1000 |
| 7 | PASS_A | 0 | 0000 | 01 | 0001 |
| 8 | PASS_B | 0 | 0000 | 01 | 0001 |
| 9 | INC | 1 | 0000 | 00 | 0000 |
| 10 | DEC | 0 | 1111 | 00 | 0000 |
| 11 | CMP | 1 | 0011 | 00 | 0000 |

`lgc3:0` → `net_lgc3..0` (153 mux1 C inputs). Logic ops: `s0|s1` → **157_YBP** selects `net_y_logic`.

---

## 3. 조합 전파 지연 (operand → Y)

예산: **250 ns** = 2.0 MHz Execute 반주기 ([`microarch-throughput.md`](microarch-throughput.md) §4).

### 3.1 opcode별 지연 · slack

<!-- TIMING_TABLE_START -->
| sel | Op | 경로 등급 | max (ns) | slack @ max (ns) | 비고 |
|-----|-----|-----------|----------|------------------|------|
| 0 | NOP | adder | **108** | 142 | sum path (Y=0) |
| 1 | ADD | adder | **108** | 142 | 283 → **157_YBP** |
| 2 | SUB | arith B-path | **136** | 114 | 153 mux2 → 283 |
| 3 | AND | logic | **46** | 204 | `U_ALU_153_0` mux1 → 157_YBP |
| 4 | OR | logic | **46** | 204 |  |
| 5 | XOR | logic | **46** | 204 |  |
| 6 | NOT | logic | **46** | 204 |  |
| 7 | PASS_A | logic | **46** | 204 | AND pattern + B=FF |
| 8 | PASS_B | logic | **46** | 204 | AND pattern + A=FF |
| 9 | INC | **critical** | **153** | 97 | `net_cin` → 283 ripple |
| 10 | DEC | adder | **108** | 142 | 283-only test path; full path = SUB class |
| 11 | CMP | arith B-path | **136** | 114 | Y = SUB; flags §3.5 |
<!-- TIMING_TABLE_END -->

측정: [`alu8_opcode_timing`](../../hw/tests/alu8_opcode_timing.yaml) · pre-flight sim artifact `alu8_opcode_timing/timing_report.json` (@ **max**).

**worst-case (Y):** **INC** — **153 ns** (slack **97 ns** @ 250 ns).  
**SUB / CMP:** **136 ns** (slack **114 ns**).  
**fastest:** logic opcodes — **46 ns**.

**Comb-limited Fmax (INC 기준):** \(F \approx 1 / (2 \times 153\,\text{ns}) \approx 3.3\,\text{MHz}\). 명목 **2 MHz:** slack = 250 − 153 = **97 ns**.

### 3.2 canonical critical path (bit0, @ max)

| Op | ref.pin hop chain |
|----|-------------------|
| **INC** | `net_cin` → `U_ALU_283_LO.C0` → `C4` → `U_ALU_283_HI.C4` → `U_ALU_157_YBP_0.1A` → `1Y` |
| **SUB / CMP** | `net_b0` → `U_ALU_153_0.B` → `2Y` → `U_ALU_283_LO.B0` → `C4` → `U_ALU_283_HI.C4` → `U_ALU_157_YBP_0.1A` → `1Y` |
| **ADD / NOP / DEC*** | `U_ALU_283_LO.A0` → `C4` → `U_ALU_283_HI.C4` → `U_ALU_157_YBP_0.1A` → `1Y` |
| **AND / OR / XOR / NOT / PASS** | `U_ALU_153_0.1Y` → `U_ALU_157_YBP_0.4B` → `4Y` |

\* DEC timing vector uses 283-only path; normative full datapath delay class = SUB (**136 ns**).

### 3.3 ACC 래치 (Y → 574.Q)

B3c 브링업 경로 — ALU 출력이 **다음 posedge** 전에 setup 만족해야 함.

| 구간 | typ (ns) | max (ns) | slack @ max (ns) |
|------|----------|----------|------------------|
| `157_YBP_0.1Y` → `574_ACC.D0` (+ setup) | 17 | 28 | 222 |

전체 **operand → ACC.Q** (max): INC 기준 **153 + 23 (574 t_pd)** ≈ **176 ns** (ACC.Q 직결 A-side, CPLD async read 미포함).

### 3.5 CMP 플래그 (SUB 유도, no 7485)

`ALU_CMP_SUB`: CMP/SUB 시 (`bctrl` SUB pattern, `cin=1`) **Z** = all `net_y==0`, **C_GE** = `net_c_hi`.  
pre-flight sim [`alu8_cmp_sub`](../../hw/tests/alu8_cmp_sub.yaml) — 플래그 behavioral 상한 **151 ns** @ max (`74hc.yaml` `ALU_CMP_SUB`); pin-chain SUB Y = **136 ns**.

| 구간 | typ (ns) | max (ns) | 비고 |
|------|----------|----------|------|
| `net_b0` → `net_cmp_z` | — | **≤151** | behavioral upper bound |
| `net_b0` → `net_cmp_c_ge` | — | **≤151** | via `net_c_hi` @ 283 |

실기: `net_cmp_z` / `net_cmp_c_ge` → FLG 574 또는 CPLD; Execute 말 샘플 ([`alu8.md`](../../hw/netlist/blocks/alu8.md)).

### 3.4 CPLD FSM E2E (v1.0 SoC)

v1.0 CPU는 **FSM-only idx5** — Flash **`$4000` CW 미사용** ([control-and-decode.md](control-and-decode.md)). ALU comb 경로는 M1과 동일하며, Execute 예산에 **CPLD async GPR read** (~10–15 ns typ)만 직렬 가산.

| 구간 | typ (ns) | max (ns) | 비고 |
|------|----------|----------|------|
| CPLD `q_a`/`q_b` → ALU A/B | 10 | 15 | [`cpld.yaml`](../../hw/timing/cpld.yaml) |
| ALU comb (worst INC) | — | **153** | §3.1 |
| ALU comb (SUB/CMP Y) | — | **136** | §3.1 |
| Y → 574 latch setup | 17 | 28 | §3.3 |

---

## 4. pre-flight sim 검증 · 파형 측정

| 테스트 | 검증 opcode / 구간 | 리포트 delay (max) |
|--------|-------------------|-------------------|
| [`alu8_full`](../../hw/tests/alu8_full.yaml) | 12 opcode 기능 | — |
| [`alu8_opcode_timing`](../../hw/tests/alu8_opcode_timing.yaml) | 12 opcode slack | INC **153**, SUB **136**, logic **46**, ADD **108** |
| [`alu8_timing`](../../hw/tests/alu8_timing.yaml) | ADD carry · logic hop | ADD **108** ns, `U_ALU_153_0` logic **46** ns |
| [`alu8_cmp_sub`](../../hw/tests/alu8_cmp_sub.yaml) | CMP flags | behavioral **≤151** ns |
| [`alu_b3_sub_critical`](../../hw/tests/alu_b3_sub_critical.yaml) | SUB | **136** ns @ max; slack **114** ns |
| [`alu_b3_xor_critical`](../../hw/tests/alu_b3_xor_critical.yaml) | XOR | **46** ns |
| [`alu_b3_latch`](../../hw/tests/alu_b3_latch.yaml) | ACC setup | **51** ns (153→574 CP) |
| [`alu283_carry`](../../hw/tests/alu283_carry.yaml) | 283 only | ripple **90** ns |

---

## 5. CPU 맥락 — 명령 “지연” (macro-cycle)

ALU 블록 자체는 **순수 조합**입니다. ISA 수준 지연은 FSM phase에 따릅니다.

| 계층 | 지연 | 설명 |
|------|------|------|
| ALU comb | **≤ 153 ns** | 위 §3 — Execute 반주기 250 ns **내** (worst INC) |
| Execute phase | **1 macro-half** (250 ns) | CPLD FSM + regfile + ALU + ACC latch |
| ALU-only µop (예: `ADD TMP`) | **1 Execute** | fetch 없음 — [microcode-spec.md](microcode-spec.md) §3.1 |
| Fetch+Execute 명령 | **2 macro-cycle** (1.0 µs) | T1 fetch + T3 exec — [microarch-throughput](microarch-throughput.md) §3.5 |
| 시스템 클록 | **2.0 MHz** | 500 ns macro-cycle, **250 ns** φ_fetch / φ_exec |

CPU E2E (Flash program fetch + CPLD read + ALU)는 별도 `cpu_v1_*` / `cpld_regfile_dual_read` 게이트 — ALU Y 기여분 상한 **INC 153 ns**, **SUB 136 ns**; logic **46 ns**.

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
| 2026-07-04 | v1.4: INC **153** / SUB **136** ns; `inc` 열 제거; M1 vs SoC decode header; Flash CW § 삭제 → CPLD FSM E2E |
| 2026-07-03 | Bit-slice `U_ALU_153_0..7` + AB bus; timing paths updated |
| 2026-06-02 | Phase B2: Gigatron logic, **12 DIP**, opcode timing matrix, logic **46 ns** |
| 2026-06-02 | Phase B1: `157_B2` 제거, `157_YBP` sum bypass |
| 2026-06-01 | 12 opcode · 제어 · typ/max 지연 · pre-flight sim 교차표 초판 |
