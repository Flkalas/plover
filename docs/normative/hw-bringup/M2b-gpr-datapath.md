# M2b — CPLD GPR datapath (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M2b (datapath) |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) v1.0 |
| **Goal** | **CPLD-only** R0/R1/R2 + fixed read + FSM ADD (no external 574 GPR, no decode block) |

---

## 1. 아키텍처 요약

| 항목 | v1.0 |
|------|-------|
| GPR | **ATF1504 내부** R0, R1, R2 |
| Read | **고정:** R0→`q_a`, R1→`q_b` |
| Write | `REG_WE` + `REG_WSEL[1:0]` (default R2) |
| ALU ctrl | CPLD FSM → `cin`/`b_sel`/`lgc*`/`y_mux` **직접** |
| Decode | **없음** — `alu8_decode` SoC 미장착 |

공유 버스: `net_d0..7` — [breadboard-wiring.md](breadboard-wiring.md).

---

## 2. CPLD ↔ ALU 결선

| CPLD 출력 | ALU 입력 |
|-----------|----------|
| `q_a0..7` | `net_a0..7` |
| `q_b0..7` | `net_b0..7` |
| `cin`, `b_sel`, `b_const_sel` | 283 / 153_B |
| `lgc3..0` | 153_L |
| `y_mux_sel` | 157_YBP select |

| ALU 출력 | 목적지 |
|----------|--------|
| `net_y0..7` | 버스 (`Y_OE` 시) → CPLD `d_in` (GPR write) |

---

## 3. GPR 쓰기 규칙

```text
REG_WE=1 @ CLK↑ → regs(REG_WSEL) <= d_in
```

- 한 사이클에 **REG_WE 1회**만 (FSM 보장).
- `d_in` 구동원: ALU Y (`Y_OE=1`) 또는 SRAM (`MEM_RD=1` via 245).

---

## 4. 단계별 실장 (G0–G5)

### G0 — CPLD in-system

**작업:** M2a에서 검증한 CPLD를 CPU 보드에 장착. `q_a`/`q_b` → ALU A/B. ALU ctrl CPLD → alu8.

**Pass:** M2a 벤치 ADD ph0에서 `q_a` LED = R0 패턴.

---

### G1 — R0/R1 프리로드

**작업:**

1. Bench: `REG_WSEL=00`, `REG_WE` 수동 + `d_in` DIP → R0에 `0x12` 래치.
2. `REG_WSEL=01` → R1에 `0x34` 래치.

**Pass:** scope/DIP readback으로 R0/R1 확인 (또는 다음 단계 q_a/q_b 관측).

---

### G2 — 고정 read path

**작업:** R0=`0x12`, R1=`0x34` 상태에서 `q_a`/`q_b` 프로브.

**Pass:** `q_a`=`0x12`, `q_b`=`0x34` (async, ~10 ns typ).

---

### G3 — ALU 피연산자

**작업:** FSM ph0/ph1 또는 수동 ALU ctrl로 SUB 경로 스모크.

**Pass:** ALU Y = R0 − R1 (플래그만 관측 가능).

---

### G4 — R2 쓰기

**작업:** `Y_OE=1`, ALU ADD 결과를 `d_in`으로, `REG_WE=1`, `REG_WSEL=10` (R2).

**Pass:** R2 readback (via 다음 write to R0 + q_a) = ALU Y.

---

### G5 — FSM ADD 3-phase

**작업:**

1. R0=`0x12`, R1=`0x34` 프리로드.
2. `OPC=0x01` (ADD), FSM 자동 3 phase @ `net_clk2`.
3. 관측: R2 = `0x46`.

**Pass:** scope에서 3 phase strobes; R2=`0x46`. pre-flight sim: `cpld_seq_add.yaml`.

**게이트:** 각 Execute 반주기 **≤250 ns** ([alu-opcodes-timing.md](../hardware/alu-opcodes-timing.md)).

---

## 5. 버스 규칙

동시에 **한 구동원만** `net_d0..7` 구동:

| 구동원 | Enable |
|--------|--------|
| ALU Y | `Y_OE`=1 |
| SRAM | `MEM_RD`=1 (245 경유) |

---

## 6. 고장 분리

| 증상 | 조치 |
|------|------|
| q_a ≠ R0 | 고정 read VHDL; R0 미래치 |
| ADD 틀림 | `cin`/`b_sel` FSM 테이블 |
| 버스 충돌 | `Y_OE`와 `MEM_RD` 동시 1 금지 |

---

## 7. 다음

→ [M2b-memory.md](M2b-memory.md) · [M3a-control-store.md](M3a-control-store.md)
