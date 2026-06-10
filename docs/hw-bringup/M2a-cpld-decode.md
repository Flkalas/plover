# M2a — CPLD system decode bring-up (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | ATF1504AS (100-TQFP) |
| **Goal** | JED 소각 + 벤치에서 CPLD **GPR** (`q_a`/`q_b`, `REG_SEL` from CW_H) 확인 |
| **Normative** | [cpld-system-controller.md](../cpld-system-controller.md) v1.0 |
| **hwsim** | `cpld_gpr_decode_breadboard` |

> **저장소:** ABEL/JED는 아직 리포에 없을 수 있음. 본 문서는 **배선·검증 절차**. JED 확정 후 `hw/cpld/` 에 추가.

---

## 1. 왜 M2a를 M1 다음에 하나

| 순서 | 이유 |
|------|------|
| ALU(B3a) 이후 | GPR/메모리 붙이기 전 ALU 경로 검증 |
| M2b 이전 | CPLD GPR JED로 `q_a`/`q_b` dual-read 확인 |
| CE | **138×2 + glue** — CPLD 밖 ([breadboard-wiring.md](breadboard-wiring.md)) |

**선행:** [M1-alu.md](M1-alu.md) B3a 완료 (B3b/c와 병렬 가능).

---

## 2. 필요 장비

| 항목 | 시방 |
|------|------|
| 프로그래머 | ATF1500 ISP (Atmel-ICE 등 — 데이터시트 호환 확인) |
| 소켓 | PLCC-44 → 2.54 mm DIP 어댑터 ([BOM.md](../../BOM.md) #15) |
| ISP 헤더 | 2×5, 1.27 mm JTAG, **≤10 cm** |
| 전원 | 빵판 CPU **5 V** — 프로그래머 IO 레벨 일치 |
| 벤치 | DIP 스위치, LED+1kΩ, 로직프로브, 멀티미터 |

---

## 3. ISP 배선

ATF1504 패드 배치는 **사용 어댑터 데이터시트**와 대조.

| 신호 | 기능 |
|------|------|
| TCK | 테스트 클록 |
| TMS | 모드 선택 |
| TDI / TDO | 데이터 |
| VCC / GND | 타깃 전원 (소각 시 칩에 5 V 인가) |

- CPLD VCC–GND **0.1 µF** 최단 (어댑터 4면).
- ISP 케이블을 **2 MHz 클록 트리에서 멀리**.

---

## 4. 설계·소각 절차

### 4.1 HDL 구현 체크리스트

[cpld-system-controller.md](../cpld-system-controller.md) §2–§6:

- [ ] `LOAD_R0..3` ← `REG_WE` ∧ Reg_Sel 디코드
- [ ] `Reg_Sel[1:0]` ← `opcode[3:0]`, `phase[1:0]` ([microcode-spec.md](../microcode-spec.md) · [`reg_sel.py`](../../hw/micro/reg_sel.py))
- [ ] `RESET_N=0` → `ADDR_FORCE_FFFC`
- [ ] `MAILBOX_EN` = `$FF00–$FFFB` 만; `$FFFC` 제외
- [ ] RAM1/RAM2 CS — [memory-map.md](../memory-map.md)

```vhdl
LOAD_R0 <= (not Reg_Sel(1) and not Reg_Sel(0)) and REG_WE;
LOAD_R1 <= (not Reg_Sel(1) and     Reg_Sel(0)) and REG_WE;
LOAD_R2 <= (    Reg_Sel(1) and not Reg_Sel(0)) and REG_WE;
LOAD_R3 <= (    Reg_Sel(1) and     Reg_Sel(0)) and REG_WE;
```

### 4.2 핀 락

`hw/netlist/blocks/cpld_system_ctrl.yaml` 넷 이름 ↔ CPLD 패드 1:1 표 → `hw/cpld/system_ctrl.pin`.

### 4.3 소각

1. Fit (매크로셀 ≤ 64)
2. JED 생성
3. Erase → Program → **Verify PASS**
4. (권장) Blank check 후 1회 재소각

산출물: `hw/cpld/system_ctrl.jed`, `hw/cpld/README.md` (툴·명령 기록).

---

## 5. 벤치 검증 — CPLD 단독 (574/ALU 미연결)

CPLD 출력에 **LED**를 달고, 입력은 **DIP**로 만듭니다.

### 5.1 벤치 보드 구성

| CPLD 입력 (DIP) | 비트 | 용도 |
|-----------------|------|------|
| `net_opc0..3` | opcode | ADD = `0x01` → opc0=**1**, opc1=0, opc2=0, opc3=0 |
| `net_ph0..1` | phase | 0=00, 1=01, 2=10, 3=11 |
| `net_reg_we` | 1bit | CW B3 — 래치 사이클에서 1 |
| `net_reset_n` | 1bit | 0=RESET assert |
| `net_map_mode` | 1bit | 0=Boot, 1=Run |
| `net_a0..15` | 주소 | 메모리 디코드 스모크 |

| CPLD 출력 (LED) | 관측 |
|-----------------|------|
| `net_load_r0..3` | 한 번에 하나만 켜져야 함 |
| `net_reg_sel0..1` | Reg_Sel 값 |
| `net_addr_force_fffc` | RESET 시 1 |
| `net_ram1_cs_n` 등 | 메모리 CS |

### 5.2 ADD opcode × phase 워크스루

hwsim 벡터 [`cpld_gpr_decode.yaml`](../../hw/tests/cpld_gpr_decode.yaml) 와 **동일**하게 설정:

| 단계 | opc | phase (ph1 ph0) | REG_WE | 기대 REG_SEL | 기대 LOAD_R* |
|------|-----|-------------------|--------|--------------|--------------|
| 1 | `01` | 00 | 0 | 00 | 모두 0 |
| 2 | `01` | 01 | 0 | 01 | 모두 0 |
| 3 | `01` | 10 | **1** | 10 | **LOAD_R2=1** 만 |

**단계 3 Pass:** R2 LED만 ON, R0/R1/R3 LED OFF.

### 5.3 RESET 스모크

| 조건 | 기대 |
|------|------|
| `RESET_N=0` (버튼 누름) | `ADDR_FORCE_FFFC` LED ON |
| `RESET_N=1` | LED OFF |

### 5.4 메모리 디코드 스모크

주소 DIP `net_a0..15` (리틀엔디안 비트 순):

| 주소 (hex) | MAP_MODE | RESET_N | 측정 | 기대 |
|------------|----------|---------|------|------|
| `$0100` | 0 (Boot) | 1 | `RAM1_CS_N` | 활성(로우) |
| `$FF04` | 0 | 1 | `MAILBOX_EN` | 1 |
| `$FFFC` | 0 | 1 | `MAILBOX_EN` | **0** |
| any | any | 0 | addr override | `$FFFC` 경로 |

상세: [memory-map.md](../memory-map.md).

### 5.5 hwsim Gate (배선 전·후)

```bash
python -m hwsim run hw/tests/cpld_gpr_decode.yaml
python -m hwsim run hw/tests/mem_decode.yaml
```

---

## 6. M2a sign-off

- [ ] Programmer Verify PASS
- [ ] 벤치 단계 3: ADD ph2 + REG_WE → LOAD_R2만 ON
- [ ] RESET → ADDR_FORCE_FFFC ON
- [ ] `$FF04` mailbox ON, `$FFFC` mailbox OFF
- [ ] hwsim 2종 PASS
- [ ] `hw/cpld/README.md`에 소각 명령 기록

---

## 7. 고장 분리

| 증상 | 조치 |
|------|------|
| Verify 실패 | 전원, JTAG 길이, IO 5 V |
| 출력 플로팅 | JED/핀 락 불일치 |
| LOAD_R* 전부 0 | REG_WE 미연결, PLA 누락 |
| RAM CS 반전 | active-low 의도 확인 |

---

## 8. 다음

→ [M2b-gpr-memory.md](M2b-gpr-memory.md)
