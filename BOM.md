# Plover — 구매 목록 (v0.1, 1세트)

| 항목 | 값 |
|------|-----|
| **설계** | **v0.1** — [system-architecture.md](docs/system-architecture.md) |
| **용도** | **5 V** 74HC 브레드보드 — 이 표만 보고 부품 구매·조립 |
| **수량** | 프로토타입 **1대** (74HC CPU + CPLD + Flash/SRAM + 클록) |
| **개정** | 2026-06-02 |

**PCB · 단일 3.3 V 버전:** [BOM-3v3.md](BOM-3v3.md) — **동일 v0.1 시스템** (74LVC SMD · 레벨시프트 없음). 빵판 본 문서와 **중복 주문 금지**.  
명세·결선·타이밍: [microcode-spec.md](docs/microcode-spec.md) · [cpld-system-controller.md](docs/cpld-system-controller.md) · [hw/netlist/](hw/netlist/).  
발주 이력(참고): [1차](docs/purchase-devicesmart.md) · [2차](docs/purchase-2026-06-01-followup.md).

열: **MPN** = 주문 품번 · **Qty** = 1세트 수량 · **시스템에서 하는 일** = 없으면 막히는 동작

---

## 인프라 · 배선

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 1 | SZH-BBAD-002 | Breadboard 830-pin MB-102 | 4 | CPU·ALU·메모리·CPLD 블록을 **병렬 결선**할 면적 |
| 2 | *(0.6 mm solid wire)* | 3-color jumper wire 1 m | 6 | 점퍼·버스·전원 **물리 배선** |
| 3a | *(SOP28/SSOP28 dual)* | SOP28↔DIP adapter | 2 | **IS62C256** SOP-28 ×2 |
| 3b | *(TSOP-32→DIP)* | TSOP-32↔DIP adapter | 1 | **SST39SF010** (4C-PHE) — SOP28 **불가** |
| 3c | *(SOIC-24→DIP)* | SOIC-24↔DIP adapter | 3 | **SN74LVC8T245** DWR ×3 (5 V↔3.3 V) |

---

## ALU (74HC, 22 IC)

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 4 | 74HC283N | 4-bit full adder | 2 | 8비트 **ADD/SUB** 캐리 연쇄 |
| 5 | 74HC153 | Dual 4-to-1 MUX | 4 | ALU 내부 **데이터 경로** 선택 |
| 6 | 74HC86 | Quad XOR | 4 | **SUB / XOR** |
| 7 | 74HC08 | Quad AND | 2 | **AND** |
| 8 | 74HC32 | Quad OR | 2 | **OR** |
| 9 | 74HC157 | Quad 2-to-1 MUX | 6 | 피연산자 B/~B, INC/DEC, ALU **출력 MUX** |
| 10 | 74HC04 | Hex inverter | 2 | 8비트 **NOT (~A)** |

---

## CPU 데이터패스 (GPR = 574×4)

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 11 | 74HC574 | Octal D latch 3-state | 7 | **MBR, PCH, FLG + R0–R3** — 명령이 쓰는 레지스터 |
| 12 | 74HC161 | 4-bit counter | 3 | **PCL×2**, 실행 **phase** 카운터 |
| 13 | 74HC157 | Quad 2-to-1 MUX | 2 | 주소 버스 **A[7:0] MUX** (addr_mux) |

---

## 시스템 CPLD · 맵 스위치

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 14 | ATF1504AS-10JU44 | CPLD 64-macrocell | 1 | ROM/RAM/메일박스 **디코드**, 버스 **arb**, `LOAD_R0..3` |
| 15 | *(PLCC-44→DIP-44)* | PLCC socket → 2.54 mm DIP | 1 | CPLD를 **브레드보드**에 실장 |
| 16 | *(DIP-1 switch)* | MAP_MODE Boot/Run | 1 | **Boot** (`$0000–$07FF` ROM) ↔ **Run** (RAM) — 운영자만 전환 ([memory-map.md](docs/memory-map.md)) |

---

## 버스 · 메모리

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 17 | 74HC245 | Octal bus transceiver | 1 | **SRAM ↔ MBR** 데이터 버스 방향 |
| 18 | SST39SF010A-70-4C-PHE | 128K×8 NOR Flash | 1 | **부트**, 8b CW, 유틸리티 ROM ([rom-architecture.md](docs/rom-architecture.md)) |
| 19 | IS62C256AL-45ULI-TR | 32K×8 SRAM | 2 | **64 KB** (A15 뱅크) · 커널·스택·벡터 RAM |

---

## 클록 (4 MHz → 2 MHz)

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 20 | *(4 MHz half-can osc)* | Crystal oscillator 4.000 MHz | 1 | 마스터 클록 (**HC-49 half**) |
| 21 | 74HC74 | Dual D flip-flop | 1 | **÷2 → 2 MHz**, 50% duty |
| 22 | 74HC04 | Hex inverter | 1 | 클록 **버퍼 / 보수** (ALU용 04와 별도 1개) |
| 23 | 74HC14 | Hex Schmitt inverter | 2 | 클록 트리, **엣지 정형** (M7 타이밍) |

*74HC04 합계 **3개** (ALU #10 ×2 + 클록 #22 ×1). 74HC157 합계 **8개** (ALU #9 ×6 + CPU #13 ×2).*

---

## 레벨 시프트 (5 V CPU ↔ 3.3 V SMD)

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 24 | SN74LVC8T245DWR | 8-bit dual-supply transceiver | 3 | **Nano · Flash · CPLD** — VCCA=5 V, VCCB=3.3 V (SOIC→#3c) |

*5 V 빵판 CPU에 RP2350만 추가: [BOM-3v3.md 부록](BOM-3v3.md#부록-5-v-빵판-cpu--rp2350-만-연결). PCB 통합 시: [BOM-3v3.md](BOM-3v3.md) §RP2350.*

---

## 전원 · Flash 프로그래밍

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 25 | PWR080015 | Breadboard 5 V / 3.3 V supply | 1 | **듀얼 레일** (74HC 5 V + SMD 3.3 V) |
| 26 | SZH-CAB28 | Micro-B USB cable 1 m | 1 | Nano·모듈 **USB 전원/통신** |
| 27 | THC-NAO002 | Arduino Nano V3 CH340 (USB-C) | 1 | NOR Flash **CW 비트뱅** 프로그래밍 |
| 28 | 74HC595 | 8-bit shift register | 3 | Flash 프로그램 시 **주소 확장** |

---

## 패시브 · 신호 무결성

| # | MPN | Description | Qty | 시스템에서 하는 일 |
|---|-----|-------------|-----|-------------------|
| 29 | *(Mono 0.1 µF Y5V 50 V)* | Decoupling 0.1 µF | **42** | 74HC DIP **38** + CPLD **4** ([검산](#수량-검산) · #3 어댑터별 +1 권장 **+6**) |
| 30 | *(Dip tantal 10 µF 35 V)* | Bulk 10 µF | 10 | VCC **벌크 디커플** |
| 31 | *(E/C 63 V 10 µF 105 °C)* | Electrolytic 10 µF | 10 | 리플·**POR** |
| 32 | BMI-BEAD-3590L | Ferrite bead | 10 | 전원 **고주파 필터** |
| 33 | *(8×330 Ω SIP)* | 33 Ω ×8 bus series | 10 | 데이터 버스 **종단/시리즈** |
| 34 | Bourns 4708-103-103LF | 8×10 kΩ SIP pull-up | 10 | 버스 **풀업** |
| 35 | *(1/4 W 103F 10 kΩ 1%)* | Axial 10 kΩ | 10 | 풀업·RC |
| 36 | 1N4148 | Switching diode | 10 | POR·**클램프** |

---

## 조립 전 필수 (부품 1개가 아닌 장비)

| MPN | Description | Qty | 시스템에서 하는 일 |
|-----|-------------|-----|-------------------|
| *(ATF1504 JTAG/ISP)* | CPLD programmer | 1 | ATF1504에 **시스템 decode 비트스트림** 소각 — 없으면 CPLD 미동작 |
| *(선택)* | RESET 푸시 버튼 + 풀업 | 1 | **RESET_N** — 전원 인가 후 `$FFFC` 페치 ([bootloader.md](docs/bootloader.md)) |

합성·비트스트림: [cpld-system-controller.md](docs/cpld-system-controller.md). Flash 이미지: [rom-architecture.md](docs/rom-architecture.md).

---

## 본 목록에 없음 (별도)

| 항목 | 이유 |
|------|------|
| **RP2350B** 코프로 | 빵판: 부록 LVC245×1 · PCB 통합: [BOM-3v3.md](BOM-3v3.md) |
| **alu8_decode PLA** | 시뮬 전용 — 실기는 **Flash 8b CW** |

---

## 합계 (참고)

| 구분 | 수량 |
|------|------|
| 표 라인 (#1–#36, #3a–c) | 38종 |
| 74HC DIP IC | **42** (ALU 22 + CPU 12 + 버스 1 + 클록 4 + 595×3) |
| 74HC157 / 74HC04 | 각 **8** / **3** (표 #9+#13, #10+#22) |
| SMD (+ #3 어댑터) | Flash×1, SRAM×2, LVC245×3, CPLD×1 |

---

## 수량 검산

v0.1 [system-architecture.md](docs/system-architecture.md) · [alu8.md](hw/netlist/blocks/alu8.md) · 구매 이력과 대조.

### 74HC — 표와 일치 ✓

| 블록 | 산식 | 합계 |
|------|------|------|
| ALU | 283×2 + 153×4 + 86×4 + 08×2 + 32×2 + 157×6 + 04×2 | **22** |
| CPU | 574×7 + 161×3 + 157×2 | **12** |
| 버스 | 245×1 | **1** |
| 클록 | 74×1 + 04×1 + 14×2 | **4** |
| Flash prog | 595×3 | **3** |
| **합계** | | **42** |

### 많이 사는 품목 — 주의

| # | 표 Qty | 검산 | 비고 |
|---|--------|------|------|
| **0.1 µF** | **42** | 74HC **38** (42−595×3) + CPLD **4** | 어댑터 **+6** 여유 권장 |
| **SMD 어댑터** | **6** (#3a+b+c) | SRAM 2 + Flash 1 + LVC 3 | |
| 10 µF / bead / SIP / axial | 각 **10** | 설계 여유 | |
| 브레드보드 ×4 · 점퍼 6 m | | ✓ | |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-02 | [BOM-3v3.md](BOM-3v3.md) = PCB 3.3 V 대응 명세로 정의 |
| 2026-06-01 | 수량 검산 · 어댑터 6 · 0.1 µF 42 |
| 2026-06-01 | 완전 구매 목록 + 항목별 시스템 의도 |
