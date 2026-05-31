# CPLD hybrid register file — v1.3

> **Superseded by [cpld-system-controller-v2.0.md](cpld-system-controller-v2.0.md)** — v2 uses **external 574×4 GPR**; ATF1504AS is **system controller** only.

**ATF1504AS-10JU44** 한 장으로 8비트 4-GPR 듀얼 포트 레지스터 파일을 구현하는 하이브리드 CPU 경로입니다.  
디스크리트 `74HC574×4` GPR 및 `74HC157/153` B-side MUX를 CPLD 내부 논리로 대체합니다.

**관련:** [BOM.md](../BOM.md) · [arch-bom-tradeoffs §8](arch-bom-tradeoffs-v1.1.md) · hwsim [`cpld_regfile.yaml`](../hw/netlist/blocks/cpld_regfile.yaml)

---

## BOM 변동 (JTAG 프로그래머 제외)

| 부품 | Δ | 목적 |
|------|---|------|
| **ATF1504AS-10JU44** | +1 | 4-GPR 듀얼 포트 regfile (Port A/B) |
| **PLCC-44 → DIP-44 어댑터** | +1 | SMD PLCC를 2.54 mm 브레드보드에 장착 |
| **0.1 µF 모노** | +4 | CPLD VCC/GND 핀헤더 국소 디커플링 (SSO 억제) |
| **74HC574 (DIP)** | −4 | R0–R3 개별 래치 제거 |
| **74HC157 / 74HC153** | −4 ~ −8 | ALU B-input / regfile MUX 디스크리트 제거 |

**별도 구매 (BOM 미포함):** 5 V 호환 JTAG ISP 케이블 (ATATMEL-ICE, USB Blaster 등) — 실장 시 CPLD 합성·다운로드에 필요.

---

## hwsim 추상화

디스크리트 `acc_reg`, `tmp_reg`, `alu_b_mux` 대신 단일 **`CPLD_REGFILE`** 블록:

| 포트 | 방향 | 설명 |
|------|------|------|
| `clk` | in | 시스템 마스터 클록 |
| `we` | in | 쓰기 enable |
| `r_sel_a[1:0]`, `r_sel_b[1:0]` | in | 읽기 포트 A/B 주소 (R0–R3) |
| `w_sel[1:0]` | in | 쓰기 주소 |
| `d_in[7:0]` | in | 쓰기 데이터 |
| `q_a[7:0]`, `q_b[7:0]` | out | 비동기 읽기 (조합) |

### 타이밍 (behavioral)

- **읽기:** `r_sel_*` 변경 후 **`t_pd` = 10 ns** (typ) — 클록 비종속 조합 출력.
- **쓰기:** `we=1`일 때 `clk` ↑ 에지에서 `w_sel` 위치에 `d_in` 래치; setup **5 ns** (typ).

타이밍 상수: [`hw/timing/cpld.yaml`](../hw/timing/cpld.yaml)  
모델: [`hwsim/models/base.py`](../hwsim/models/base.py) `CpldRegfile`  
검증: [`hw/tests/cpld_regfile_dual_read.yaml`](../hw/tests/cpld_regfile_dual_read.yaml)

---

## ALU 연결 (목표 top-level)

```
         ┌────────────────── ATF1504AS ──────────────────┐
  clk ──►│  R0 R1 R2 R3  (sync write @ we∧clk↑)        │
  we  ──►│       ▲              │                       │
 w_sel ──►│       │         q_a ──────► ALU A[7:0]      │
  d_in ──►│       d_in         q_b ──────► ALU B[7:0]    │
r_sel_a ─►│  async read A                                │
r_sel_b ─►│  async read B                                │
         └──────────────────────────────────────────────┘
```

- **제거:** `alu_b_mux`, 개별 `574` GPR, regfile용 `157/153`.
- **유지:** ALU B3 (`alu8`), fetch/MBR/PCL/PCH 등 v1.1/v1.2 CPU 골격 (574 일부는 MBR·PCH 등 비-GPR 용도).

---

## 물리·bring-up 주의

1. **SSO:** Port A/B 16비트 동시 스위칭 시 VCC 바운스 → PLCC 어댑터 **0.1 µF×4** 최단 거리 배치.
2. **JTAG:** ISP 헤더는 **짧은 배선** + GND 근접; 안테나 효과로 인접 74HC 순차 논리 간섭 가능.
3. **타이밍:** async read 10 ns는 2 MHz macro-cycle(250 ns) 내 ALU A/B setup 여유에 반영 — M7에서 critical path 재측정.

---

## v1.2 ACC+TMP와의 관계

| | v1.2 ACC+TMP | v1.3 CPLD hybrid |
|--|--------------|------------------|
| GPR | ACC+TMP (574×2) | **R0–R3 (CPLD)** |
| B-operand | 157×4 MEM\|TMP | **q_b 직결** (MUX 불필요) |
| 74HC Δ vs v1.1 | +5 (~53) | **−574×4, −157/153×4~8**, +CPLD |
| hwsim | `acc_tmp.yaml` (예정) | **`cpld_regfile` PASS** |

v1.3 채택 시 M4 CPU 통합 게이트는 **`cpld_regfile` + ALU + fetch** 경로로 전환합니다.
