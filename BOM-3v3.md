# Plover — 구매 목록 (3.3 V · PCB, v0.1)

| 항목 | 값 |
|------|-----|
| **설계** | **v0.1** — [system-architecture.md](docs/system-architecture.md) |
| **대응 명세** | [BOM.md](BOM.md) **와 동일 시스템** — 실장·전기만 다름 |
| **용도** | **단일 3.3 V** · **PCB SMD** — Fab·픽·조립용 |
| **수량** | 프로토타입 **1대** |
| **개정** | 2026-06-02 |

**5 V 74HC 브레드보드:** [BOM.md](BOM.md) — **중복 주문 금지** (빵판·DIP·`LVC8T245×3`는 본 PCB BOM에 **없음**).

| | [BOM.md](BOM.md) | 본 문서 |
|---|------------------|---------|
| 전원 | 5 V + 3.3 V (듀얼) | **3.3 V 단일** |
| 논리 | 74HC **DIP** | **SN74LVC** TSSOP |
| 실장 | 빵판 + 어댑터 | **PCB** 풋프린트 |
| 5↔3.3 브리지 | `LVC8T245` **×3** | **없음** |
| netlist/hwsim | `74HC` 명칭 | 동일 논리 · **3.3 V 재타이밍** 권장 |

명세: [microcode-spec.md](docs/microcode-spec.md) · [cpld-system-controller.md](docs/cpld-system-controller.md) · KiCad [hw/kicad/plover/](hw/kicad/plover/).

열: **↔** = [BOM.md](BOM.md) 동일 라인 · **Pkg** = PCB 패키지 · **Qty** = 1보드

---

## PCB · 기구

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 0 | — | *(Plover v0.1 CPU PCB)* | 2~4L FR4 | 1 | [BOM.md](BOM.md) #1–4 **대체** — 모든 SMD·커넥터 |
| 0b | — | *(스텐실, 선택)* | — | 1 | SMD 납땜 |

---

## 전원 (3.3 V 단일)

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| P1 | #25 | USB-C receptacle (USB2) | SMD | 1 | 5 V in — [BOM.md](BOM.md) PWR080015 **대체** |
| P2 | #25 | AP2112K-3.3TRG1 (또는 동급 LDO ≥600 mA) | SOT-23-5 | 1 | **3.3 V** 시스템 레일 |
| P2b | — | *(선택)* MP2359 등 Buck | SOT-23-6 | 1 | 전류·발열 여유 |
| P3 | #25,#26 | 10 µF + 22 µF | 0805 | 6 | LDO in/out · 3.3 V bulk |

---

## ALU (74LVC, 22 IC)

| # | ↔ | MPN (예: TI PWR) | Pkg | Qty | 시스템에서 하는 일 |
|---|---|------------------|-----|-----|-------------------|
| 4 | #4 | SN74LVC283APWR | TSSOP-16 | 2 | 8비트 **ADD/SUB** |
| 5 | #5 | SN74LVC153APWR | TSSOP-16 | 4 | ALU 4:1 MUX |
| 6 | #6 | SN74LVC86APWR | TSSOP-14 | 4 | SUB / XOR |
| 7 | #7 | SN74LVC08APWR | TSSOP-14 | 2 | AND |
| 8 | #8 | SN74LVC32APWR | TSSOP-14 | 2 | OR |
| 9 | #9 | SN74LVC157APWR | TSSOP-16 | 6 | B/~B, INC/DEC, out MUX |
| 10 | #10 | SN74LVC04APWR | TSSOP-14 | 2 | 8비트 **NOT (~A)** |

---

## CPU 데이터패스

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 11 | #11 | SN74LVC574APWR | TSSOP-20 | 7 | MBR, PCH, FLG, **R0–R3** |
| 12 | #12 | SN74LVC161APWR | TSSOP-16 | 3 | PCL×2, **phase** |
| 13 | #13 | SN74LVC157APWR | TSSOP-16 | 2 | **A[7:0]** addr MUX |

---

## 시스템 CPLD · 운영

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 14 | #14 | ATF1504AS-10JU44 | **PLCC-44** | 1 | decode · `LOAD_R0..3` |
| 15 | #15 | *(JTAG 2×5 1.27 mm)* | TH | 1 | CPLD ISP — [BOM.md](BOM.md) PLCC-DIP 어댑터 **대체** |
| 16 | #16 | *(SMD slide / tact)* | SMD | 1 | **MAP_MODE** Boot/Run |
| 17 | *(조립 전)* | *(Tact RESET + 10 kΩ 0603)* | SMD | 1 | **RESET_N** |

---

## 버스 · 메모리

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 18 | #17 | SN74LVC245APWR | TSSOP-20 | 1 | SRAM ↔ MBR (**동일 3.3 V**) |
| 19 | #18 | SST39SF010A-70-4C-PHE | **TSOP-32** | 1 | Boot · 8b CW · ROM |
| 20 | #19 | IS62C256AL-45ULI-TR | **SOP-28** | 2 | 64 KB (A15) |

*품번 **4C** / **AL** 유지 — [BOM.md](BOM.md)와 동일.*

---

## 클록 (4 MHz → 2 MHz)

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 21 | #20 | *(4.000 MHz, 3.3 V CMOS XO)* | 3225/5032 | 1 | 마스터 클록 — **5 V half-can 아님** |
| 22 | #21 | SN74LVC74APWR | TSSOP-14 | 1 | ÷2 → **2 MHz** |
| 23 | #22 | SN74LVC04APWR | TSSOP-14 | 1 | clk buffer |
| 24 | #23 | SN74LVC14APWR | TSSOP-14 | 2 | Schmitt · clk tree |

*`SN74LVC04` **3** (#10×2 + #23). `SN74LVC157` **8** (#9×6 + #13×2).*

---

## 레벨 시프트

| # | ↔ | MPN | Qty | 비고 |
|---|---|-----|-----|------|
| — | #24 | SN74LVC8T245DWR | **0** | 단일 3.3 V — [BOM.md](BOM.md) #24 **해당 없음** |

---

## 전원 · Flash 프로그래밍

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 25 | #27 | *(Prog 헤더 / USB-C UART)* | TH/SMD | 1 | Flash CW — [BOM.md](BOM.md) Nano **대체·병행** |
| 26 | #26 | *(선택)* Pico / CH340 모듈 소켓 | — | 1 | 개발용 비트뱅 |
| 27 | #28 | SN74LVC595APWR | TSSOP-16 | 3 | Flash 주소 시프트 |

---

## 패시브 · 신호 무결성 (SMD)

| # | ↔ | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|---|-----|-----|-----|-------------------|
| 29 | #29 | 0.1 µF 50 V X7R | **0603** | **55** | IC당 1 + CPLD **+4** + 여유 ([검산](#수량-검산)) |
| 30 | #30 | 10 µF 10 V X5R | 0805 | **12** | 벌크 — [BOM.md](BOM.md) tantal **대체** |
| 31 | #31 | 10 µF 0805 또는 E-C 1206 | 0805/1206 | **4** | POR·리플 |
| 32 | #32 | Ferrite bead ~600 Ω@100 MHz | 0603 | **8** | 3.3 V 분기 |
| 33 | #33 | 33 Ω 1% | 0603 | **40** | 버스 시리즈 — [BOM.md](BOM.md) SIP×10 **대체** |
| 34 | #34 | 10 kΩ 1% | 0603 | **40** | 풀업 — [BOM.md](BOM.md) Bourns SIP **대체** |
| 35 | #35 | 10 kΩ 0603 | 0603 | *(#34에 포함)* | |
| 36 | #36 | 1N4148W | SOD-123 | **6** | POR·클램프 |

---

## 조립 전 필수

| ↔ | MPN | Qty | 시스템에서 하는 일 |
|-----|-----|-----|-------------------|
| 조립 전 | ATF1504 JTAG/ISP | 1 | CPLD 비트스트림 |
| — | SMD 납땜 · PLCC·TSOP | — | Fab 후 조립 |

---

## RP2350 코프로 (선택)

[BOM.md](BOM.md)에는 **별도 보드** 가정. PCB에 **통합** 시 **동일 3.3 V** — `LVC8T245` **불필요**.

| # | MPN | Pkg | Qty | 시스템에서 하는 일 |
|---|-----|-----|-----|-------------------|
| 40 | RP2350B | 모듈/QFN | 1 | Mailbox · vFDD ([rp2350-coprocessor.md](docs/rp2350-coprocessor.md)) |
| 41 | 0.1 µF 0603 | 0603 | 4 | RP2350 decap |

*5 V [BOM.md](BOM.md) 빵판 CPU에 코프로만 붙일 때는 `LVC8T245×1` + `AMS1117` — 아래 [부록](#부록-5-v-빵판-cpu--rp2350-만-연결).*

---

## 본 목록에 없음

| 항목 | [BOM.md](BOM.md) | 본 PCB BOM |
|------|------------------|------------|
| MB-102 · 점퍼 | #1–2 | **PCB** |
| SOP/TSOP/SOIC **어댑터** | #3a–c | **풋프린트** |
| `LVC8T245` ×3 | #24 | **삭제** |
| PWR080015 | #25 | **P1–P2** |
| alu8_decode PLA | — | Flash CW |

---

## 합계 (참고)

| 구분 | 수량 |
|------|------|
| 74LVC 패키지 | **42** (= [BOM.md](BOM.md) 74HC **42**) |
| 메모리 + CPLD | Flash×1, SRAM×2, ATF1504×1 |
| 157 / 04 합계 | **8** / **3** |

---

## 수량 검산

### 74LVC (= [BOM.md](BOM.md) 74HC)

| 블록 | 합계 |
|------|------|
| ALU | **22** |
| CPU | **12** |
| 버스 | **1** |
| 클록 | **4** |
| Prog | **3** |
| **합계** | **42** |

### 0.1 µF

| 항목 | 수 |
|------|-----|
| 42 LVC + 245 + 595 | 45 |
| Flash + SRAM×2 + CPLD | 4 |
| CPLD SSO 추가 | +4 |
| 여유 | +2 |
| **주문** | **55** |

---

## 74HC → 74LVC (픽리스트)

| [BOM.md](BOM.md) | PCB MPN |
|------------------|---------|
| 74HC283N | SN74LVC283APWR |
| 74HC153/157/161/574/245/595 | SN74LVC***APWR |
| 74HC86/08/32/04/14/74 | SN74LVC***APWR |
| 4 MHz half-can | **3.3 V** SMD XO |
| PLCC→DIP | **PLCC-44 footprint** |

---

## 부록: 5 V 빵판 CPU + RP2350 만 연결

[BOM.md](BOM.md) CPU는 그대로 두고 **코프로 보드만** 추가할 때 (본 PCB BOM **아님**):

| MPN | Qty |
|-----|-----|
| SN74LVC8T245DWR | 1 |
| AMS1117-3.3 | 1 |
| RP2350B | 1 |
| SOIC-24 adapter · 0.1 µF ×4 | |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-02 | [BOM.md](BOM.md) **PCB 3.3 V 대응 명세**로 전면 재작성 (RP2350-only 오해 수정) |
| 2026-06-01 | 최초 분리 |
