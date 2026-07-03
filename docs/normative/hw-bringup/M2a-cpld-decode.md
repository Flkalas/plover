# M2a — CPLD GPR + phase FSM bring-up (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | ATF1504AS-10JU44 (PLCC-44) |
| **Goal** | JED 소각 + 벤치에서 **3fixed GPR** + **phase FSM** 확인 |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) v1.0 |
| **pre-flight sim** | `cpld_seq_add.yaml` · `cpld_seq_tfr.yaml` · P1: `cpu_cw_direct_add.yaml` |

> **저장소:** ABEL/JED는 아직 리포에 없을 수 있음. 본 문서는 **배선·검증 절차**. JED 확정 후 `hw/cpld/` 에 추가.

---

## 1. 왜 M2a를 M1 다음에 하나

| 순서 | 이유 |
|------|------|
| ALU(B3a) 이후 | ALU 경로 검증 후 CPLD `q_a`/`q_b` 통합 |
| M2b 이전 | CPLD FSM JED로 3-phase ADD 템플릿 확인 |
| CE | **138×2 + glue** — CPLD 밖 ([breadboard-wiring.md](breadboard-wiring.md)) |
| decode | **SoC에 `alu8_decode` 없음** — ALU ctrl은 CPLD 출력 |

**선행:** [M1-alu.md](M1-alu.md) B3a 완료.

---

## 2. 필요 장비

| 항목 | 시방 |
|------|------|
| 프로그래머 | ATF1500 ISP (Atmel-ICE 등) |
| 소켓 | PLCC-44 → 2.54 mm DIP 어댑터 ([BOM.md](../../BOM.md) #15) |
| ISP 헤더 | 2×5, 1.27 mm JTAG, **≤10 cm** |
| 전원 | 빵판 CPU **5 V** |
| 벤치 | DIP 스위치, LED+1kΩ, 로직프로브, DSO (2 MHz) |

---

## 3. ISP 배선

| 신호 | 기능 |
|------|------|
| TCK / TMS / TDI / TDO | JTAG |
| VCC / GND | 타깃 전원 (소각 시 5 V) |

- CPLD VCC–GND **0.1 µF** 최단 (어댑터 4면).
- ISP 케이블을 **2 MHz 클록 트리에서 멀리**.

---

## 4. 설계·소각 절차

### 4.1 HDL 구현 체크리스트

[cpld-system-controller.md](../hardware/cpld-system-controller.md) §1–§4:

- [ ] **3fixed read:** `q_a` ← R0, `q_b` ← R1 (async)
- [ ] **Write:** `REG_WE` + `REG_WSEL[1:0]` → R0–R2 only (no R3)
- [ ] **Phase FSM:** ADD template 3 phases; `OPC[3:0]` from IR
- [ ] **ALU ctrl:** registered `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel`
- [ ] **Bus:** `Y_OE`, `MEM_RD`, `MEM_WR` registered per phase
- [ ] **Branch:** `PC_LOAD_EN` @ macro_end from `FLG_Z`/`FLG_C`
- [ ] **MC fit:** ≤ **64** macrocells (target ~32)

```vhdl
q_a <= regs(0);
q_b <= regs(1);
-- w_sel from PARAM[1:0] or FSM default R2
```

### 4.2 핀 락

`hw/netlist/blocks/cpld_system_ctrl.yaml` 넷 이름 ↔ CPLD 패드 1:1 표 → `hw/cpld/system_ctrl.pin`.

**Winner pin trim:** `OPC[3:0]` only (not full `OPC[7:0]`).

### 4.3 소각

1. Fit (MC ≤ 64)
2. JED 생성
3. Erase → Program → **Verify PASS**

산출물: `hw/cpld/system_ctrl.jed`, `hw/cpld/README.md`.

---

## 5. 벤치 검증 — CPLD + ALU (decode 블록 없음)

### 5.1 벤치 보드 구성

| CPLD 입력 (DIP) | 비트 | 용도 |
|-----------------|------|------|
| `net_opc0..3` | opcode | ADD = `0x01` |
| `net_ph0..1` | phase | FSM 내부 또는 외부 161 tap |
| `net_param0..7` | PARAM | Flash param row (bench: DIP) |
| `net_reg_we` | 1bit | FSM 출력 관측 |
| `net_flg_z`, `net_flg_c` | flags | BEQ bench |

| CPLD 출력 (LED/프로브) | 관측 |
|------------------------|------|
| `net_q_a0..7`, `net_q_b0..7` | R0/R1 async read |
| `net_cin`, `net_bctrl0..3`, `net_lgc*` | ALU ctrl (→ alu8 직결) |
| `net_y_oe`, `net_mem_rd`, `net_mem_wr` | Bus strobes |
| `net_reg_we`, `net_reg_wsel0..1` | GPR write |
| `net_pc_load_en` | Branch completion |

### 5.2 ADD 3-phase 워크스루

pre-flight sim 벡터 [`cpld_seq_add.yaml`](../../hw/tests/cpld_seq_add.yaml) 와 **동일**:

| Phase | 기대 동작 | 관측 |
|-------|-----------|------|
| 0 | R0 → ALU A; `Y_OE=1` | `q_a` = R0 값 |
| 1 | R1 → ALU B; ADD path armed | `q_b` = R1 값 |
| 2 | Execute ADD; `REG_WE=1`, `REG_WSEL=R2` | R2 latch |

**Pass:** 3 phase 각각 **250 ns** Execute 창 내 ([alu-opcodes-timing.md](../hardware/alu-opcodes-timing.md) §3.4).

### 5.3 P1 bypass (선택 — FSM 전)

`DECODE_BYPASS` 스트랩으로 Flash 16b CW → ALU 직접:

### 5.4 pre-flight sim Gate

---

## 6. M2a sign-off (P2 gate)

- [ ] Programmer Verify PASS
- [ ] MC fit report ≤ 64
- [ ] 벤치: ADD 3-phase LED/scope trace = pre-flight sim
- [ ] `q_a`/`q_b` setup before ALU comb path
- [ ] `cpld_seq_add.yaml` PASS
- [ ] `hw/cpld/README.md`에 소각 명령 기록

---

## 7. 고장 분리

| 증상 | 조치 |
|------|------|
| Verify 실패 | 전원, JTAG 길이, IO 5 V |
| `q_a`/`q_b` 플로팅 | JED/핀 락, R0/R1 미초기화 |
| ADD ph2 미래치 | FSM phase count; ALU ctrl 타이밍 |
| MC overflow | `OPC[3:0]` trim; template 단순화 |

---

## 8. 다음

→ [M2b-gpr-memory.md](M2b-gpr-memory.md)
