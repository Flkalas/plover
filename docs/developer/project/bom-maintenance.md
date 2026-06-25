# BOM 유지보수 · 검토 (v1.0 5 V 빵판)

**[BOM.md](../../../BOM.md)** 는 **쇼핑·발주 전용**입니다. 개정 이력, 수량 검산, 설계 단계(Phase) 메모, 발주 대조는 **본 문서**에 둡니다.

| 문서 | 용도 |
|------|------|
| [BOM.md](../../../BOM.md) | 무엇을 몇 개 살지 — 장바구니 |
| [parts-on-hand.md](../../normative/project/parts-on-hand.md) | **실구매 확정** — 패키지·어댑터·재주문 |
| [BOM-3v3.md](../BOM-3v3.md) | PCB 3.3 V 쇼핑 목록 |
| [purchase-devicesmart.md](purchase-devicesmart.md) | 디바이스마트 **1차** 주문 |
| [purchase-2026-06-01-followup.md](purchase-2026-06-01-followup.md) | 디바이스마트 **2·3차** · AliExpress |
| [hardware-architecture-synthesis.md](../../normative/hardware/research/hardware-architecture-synthesis.md) | 아키텍처 종합 — **v1.0 breadboard: CPLD GPR + 138×2 + 10b CW** |

---

## BOM-3v3 (PCB) 검산

### 74LVC (= [BOM.md](../../../BOM.md) 74HC)

| 블록 | 합계 |
|------|------|
| ALU | **14** |
| CPU | **12** |
| 버스 | **1** |
| 클록 | **4** |
| Flash prog (595) | **3** |
| **합계** | **34** |

| 구분 | 수량 |
|------|------|
| 74LVC IC | **34** |
| 153 / 157 / 04 | **8** / **4** / **3** |
| 0.1 µF 0603 | **47** (37 IC + 4 메모리/CPLD + 4 CPLD 여유 +2) |

### [BOM.md](../../../BOM.md) 대비 PCB에 없는 품목

| [BOM.md](../../../BOM.md) | PCB |
|---------------------|-----|
| #1–2 빵판·점퍼 | PCB #0 |
| #3a–c 어댑터 | TSOP/SOP/PLCC 풋프린트 |
| #24 LVC8T245×3 | 단일 3.3 V — **0** |
| #25 PWR080015 | P1–P3 |
| #26 Micro-B 케이블 | USB-C on board |

### 74HC → 74LVC (픽리스트)

| [BOM.md](../../../BOM.md) | PCB MPN |
|---------------------|---------|
| 74HC283N | SN74LVC283APWR |
| 74HC153 / 157 / 161 / 574 / 245 / 595 | SN74LVC***APWR |
| 74HC04 / 14 / 74 | SN74LVC***APWR |
| 4 MHz half-can (#20) | 3.3 V SMD XO |
| PLCC→DIP (#15) | PLCC-44 + JTAG TH |

### 부록: 5 V 빵판 CPU + RP2350 만 (본 PCB BOM 아님)

| MPN | Qty |
|-----|-----|
| SN74LVC8T245DWR | 1 |
| AMS1117-3.3 | 1 |
| RP2350B | 1 |
| SOIC-24 adapter · 0.1 µF ×4 | |

---

## ALU 설계 단계 (수량에 영향)

[BOM.md](../../../BOM.md) ALU는 **Phase B2 · 14 DIP IC** (7485 없음, CMP flags from SUB).

| 단계 | BOM 변화 | 효과 |
|------|----------|------|
| **Phase A/B1** | `153_B`×4, `157_YBP`×2 | SUB Y **151 ns** @ max |
| **Phase B2** | **−** `08`×2, `32`×2, `86`×2, `157_OUT`×2, `04` NOT×2 | Gigatron **`153_L`**; logic **46 ns** @ max |
| **CMP flags** | **−** `7485`×2 | **Z**=`Y==0`, **C_GE**=`net_c_hi` via SUB ([`ALU_CMP_SUB`](../hw/netlist/blocks/alu8.md)) |

Netlist · 타이밍: [alu8.md](../hw/netlist/blocks/alu8.md) · [alu-opcodes-timing.md](alu-opcodes-timing.md) · [alu8-phase-b.md](alu8-phase-b.md).

---

## 수량 검산 (74HC · 디커플링)

v1.0 [system-architecture.md](../../normative/hardware/system-architecture.md) · [alu8.md](../hw/netlist/blocks/alu8.md) 기준.

### 74HC — [BOM.md](../../../BOM.md) 표와 일치 ✓

| 블록 | 산식 | 합계 |
|------|------|------|
| ALU | 283×2 + **153×8** + **157×2** + 04×2 | **14** |
| CPU | 574×7 + 161×3 + 157×2 | **12** |
| 버스 | 245×1 | **1** |
| 클록 | 74×1 + 04×1 + 14×2 | **4** |
| Flash prog | 595×3 | **3** |
| **합계** | | **34** |

### 합계 (참고)

| 구분 | 수량 |
|------|------|
| 표 라인 (#1–#36, #3a+c) | 37종 |
| 74HC DIP IC | **34** (ALU **14** + CPU 12 + 버스 1 + 클록 4 + 595×3) |
| 74HC153 / 157 / 04 | **8** / **4** / **3** (ALU 153·157 + CPU #13, ALU·클록 04) |
| SMD (+ #3 어댑터) | Flash×1, SRAM×2, LVC245×3, CPLD×1 |

### 많이 사는 품목 — 주의

| # | [BOM.md](../../../BOM.md) Qty | 검산 | 비고 |
|---|-------------------------|------|------|
| **0.1 µF** | **38** | 74HC **30** (34−595×3) + CPLD **4** | 어댑터 **+6** 여유 권장 → **~44** |
| **SMD 어댑터** | **6** (#3a+c + #15) | SRAM 2 + LVC 3 + PLCC 1 | Flash PDIP 직결 |
| 10 µF / bead / SIP / axial | 각 **10** | 설계 여유 | |
| 브레드보드 ×4 · 점퍼 6 m | | ✓ | |

---

## 본 쇼핑 목록에 없음 (주문 금지 · 별도 BOM)

| 항목 | 비고 |
|------|------|
| **74HC7485 / 74HC85** | v1.0 ALU 미포함 |
| **RP2350B** | [BOM-3v3.md](../BOM-3v3.md) 또는 부록 |
| **alu8_decode PLA** | 시뮬 전용 |

---

## 발주 대조 (요약)

상세: [purchase-devicesmart.md](purchase-devicesmart.md) · [purchase-2026-06-01-followup.md](purchase-2026-06-01-followup.md).

| MPN | BOM | 1차+followup 누적 | 비고 |
|-----|-----|-------------------|------|
| 74HC153 | 8 | 8 (1차 4 + 주문 C 4) | ✓ ALU |
| 74HC157 | 8 | 8 | ✓ |
| ATF1504 | 1 | 1 | ✓ |
| MAP_MODE switch | 1 | 10× slide (C) | 1개 조립 |
| RESET tact | 1 (선택) | 10× (C) | ITS-1103 |
| 7485 | **0** | — | ALU 설계 미포함 |

---

## v1.0 breadboard checklist

| Item | v1.0 |
|------|------|
| CPLD package | **ATF1504AS-10JU44** PLCC-44 + #15 adapter |
| Flash package | **SST39SF010A-70-4C-PHE** PDIP-32 직결 |
| GPR | **CPLD internal** (~40 MC) |
| CE / mailbox | **74HC138×2** + 08/32/04 glue |
| CW | **10b** — 574 **CW_L + CW_H** (+ PC/MBR/FLG → **5×574** seq) |
| 138 | **2** total (+1 order from 1차) |

See [parts-on-hand.md](../../normative/project/parts-on-hand.md) · [hardware-architecture-synthesis.md](../../normative/hardware/research/hardware-architecture-synthesis.md) · [hw-bringup/breadboard-wiring.md](../../normative/hw-bringup/breadboard-wiring.md).

---

## 변경 이력

| 날짜 | 문서 | 내용 |
|------|------|------|
| 2026-06-02 | BOM·BOM-3v3 | 단일 표 · **구분** 열 내장; 검토·이력은 본 문서만 |
| 2026-06-02 | BOM | ALU **14** DIP — no 7485; 74HC **34**, decap **38** |
| 2026-06-02 | BOM-3v3 | [BOM.md](../../../BOM.md) 동기 ALU 14 IC; LVC **34**, decap **47** |
| 2026-06-02 | BOM | Phase B2 / SUB Phase A 이력 (중간 단계) |
| 2026-06-01 | BOM | 수량 검산 · 어댑터 6 |
| 2026-06-01 | BOM-3v3 | PCB 3.3 V 목록 최초 분리 |
| 2026-06-10 | parts-on-hand | v1.0 패키지 확정 — PLCC CPLD, PDIP Flash, 어댑터 검산 |
