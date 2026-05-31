# Plover v1.0 — 마이크로코드·ISA 명세 (archived)

> **Superseded by [microcode-spec-v1.1.md](microcode-spec-v1.1.md)** — ACC machine.

**버전:** 1.0 · **기준일:** 2026-05-31  
**아키텍처:** 16-bit ISA · 폰 노이만 공유 SRAM · Flash **제어 저장소** · Phase Collapsing + Shadow ACC

상세 IPC·타이밍: [microarch-throughput.md](microarch-throughput.md) · 구현 일정: [v1.0-implementation-plan.md](v1.0-implementation-plan.md)

---

## 1. 메모리 역할

| 장치 | 역할 | 주소 |
|------|------|------|
| **IS62C256** | 프로그램 + 데이터 (Von Neumann) | PC (fetch) 또는 `{R1,R0}` (execute) |
| **SST39SF010A ×2** | 16-bit **마이크로 CW** (프로그램 아님) | `{IR[15:8], phase[2:0]}` → 11-bit → 2048 words |

---

## 2. 16-bit ISA (매크로 명령)

```
IR[15:0] = { opcode[7:0], operand[7:0] }
```

| opcode (hex) | Mnemonic | 요약 |
|--------------|----------|------|
| 0x01 | ADD_IMM | Rdst ← Rdst + imm8 |
| 0x02 | LOAD | Rdst ← MEM[imm8] |
| 0x03 | STORE | MEM[imm8] ← Rsrc |
| 0x04 | BEQ | if Z: PC ← imm8 |
| 0x05 | JMP | PC ← imm8 |
| 0x06 | HALT | CP freeze |
| … | (예약) | ALU 12 opcode는 **micro-CW** `alu_op` 필드 |

operand: 즉값, 레지스터 인덱스(2-bit), 또는 PC-relative 오프셋 — opcode별 spec 부록에서 확정.

---

## 3. 사이클 FSM (Optimized — Phase Collapsing)

| Macro | 클록 | 동작 |
|-------|------|------|
| **T1 Fetch** | ↑ PC→SRAM; ↓ IR latch; Flash addr ← `{opcode,0}` | 500 ns |
| **T3 Execute** | Flash CW → datapath; phase++; MEM/ALU | 500 ns × n phases |

Baseline (T1+T2+T3)은 hwsim A/B 비교용으로만 유지. **量産 FSM = T2 생략.**

분기 taken: execute **last phase**에서 `pc_load`, `phase_rst` → next **T1**.

---

## 4. v0.2 CW 16-bit (재사용)

Flash 출력 CW는 v0.2와 **동일 필드** — `alu_op[3:0]`, `src/dst_reg`, `bus_en`, `local_ctrl`, `flg_we` 등.  
빌드: `pack_control_store.py` (M5) — opcode당 micro-phase 리스트 → hex.

---

## 5. Shadow ACC

- `74HC574` — ALU `Y` 래치 (`shadow_acc`)
- `74HC153×4` — B 입력 `b_src_sel`: SRAM data vs `shadow_acc.Q`
- B3c [`alu_b3_clock`](../hw/netlist/blocks/alu_b3_clock.yaml) 검증 경로 확장

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-31 | v1.0 초안 — Von Neumann, Collapsing, CW reuse |
