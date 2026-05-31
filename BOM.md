# Plover — Bill of Materials

| 항목 | 값 |
|------|-----|
| **설계** | **v0.1** — [system-architecture.md](docs/system-architecture.md) |
| **수량** | 프로토타입 **1세트** |
| **개정** | 2026-06-01 |
| **명세** | [microcode-spec.md](docs/microcode-spec.md) · [cpld-system-controller.md](docs/cpld-system-controller.md) |

**이 문서의 §1 표가 유일한 주문·픽·실장 기준입니다.** 아래 §2 이후는 설계 메모·변형·구매 이력입니다.

실구매 기록: [purchase-devicesmart.md](docs/purchase-devicesmart.md)

---

## §1 Procurement BOM (v0.1, 1 set)

열 정의: **MPN** = 주문·SMT 픽리스트에 넣을 품번 · **Mount** = TH(브레드보드)/SMD/Module · **Ref** = 설계 블록

| # | Category | MPN | Description | Qty | Package | Mount | Ref | Notes |
|---|----------|-----|-------------|-----|---------|-------|-----|-------|
| **인프라** |
| 1 | Mechanical | SZH-BBAD-002 | Breadboard 830-pin MB-102 | 4 | — | TH | BB | 병렬 결속 |
| 2 | Wire | *(vendor 0.6mm solid)* | 3-color jumper wire 1 m | 6 | — | — | BB | 점퍼·버스 배선 |
| 3 | Adapter | *(SOP28/SSOP28 dual)* | SOP28↔DIP adapter board | 4 | module | TH | BB | Flash·SRAM·LVC245 |
| **ALU (20× DIP 74HC)** |
| 4 | IC | 74HC283N | 4-bit binary full adder | 2 | DIP-16 | TH | alu8 | 캐리 연쇄 |
| 5 | IC | 74HC153 | Dual 4-to-1 multiplexer | 4 | DIP-16 | TH | alu8 | ALU data path |
| 6 | IC | 74HC86 | Quad 2-input XOR | 4 | DIP-14 | TH | alu8 | SUB / XOR |
| 7 | IC | 74HC08 | Quad 2-input AND | 2 | DIP-14 | TH | alu8 | AND |
| 8 | IC | 74HC32 | Quad 2-input OR | 2 | DIP-14 | TH | alu8 | OR |
| 9 | IC | 74HC157 | Quad 2-to-1 MUX | 6 | DIP-16 | TH | alu8 | B/~B, INC/DEC, out MUX |
| 10 | IC | 74HC04 | Hex inverter | 2 | DIP-14 | TH | alu8 | 8-bit NOT (~A) |
| **CPU datapath (74HC, GPR = 574×4)** |
| 11 | IC | 74HC574 | Octal D latch, 3-state | 7 | DIP-20 | TH | cpu | MBR,PCH,FLG + **R0–R3** |
| 12 | IC | 74HC161 | 4-bit sync counter | 3 | DIP-16 | TH | cpu | PCL×2, phase |
| 13 | IC | 74HC157 | Quad 2-to-1 MUX | 2 | DIP-16 | TH | addr_mux | A[7:0] address MUX |
| **System CPLD** |
| 14 | IC | ATF1504AS-10JU44 | CPLD 64-macrocell | 1 | PLCC-44 | SMD | cpld_sys | decode · arb · LOAD_R* |
| 15 | Adapter | *(PLCC-44→DIP-44)* | PLCC socket to 2.54 mm DIP | 1 | module | TH | BB | CPLD breadboard mount |
| 16 | Switch | *(DIP-1)* | MAP_MODE Boot/Run | 1 | — | TH | BB | Operator map select |
| **Bus · memory** |
| 17 | IC | 74HC245 | Octal bus transceiver | 1 | DIP-20 | TH | sram256 | SRAM ↔ MBR data |
| 18 | IC | SST39SF010A-70-4C-PHE | 128K×8 NOR Flash, 70 ns | 1 | TSOP-32 | SMD→#3 | nor_flash | boot + 8b CW + utility |
| 19 | IC | IS62C256AL-45ULI-TR | 32K×8 SRAM, 45 ns | 2 | SOP-28 | SMD→#3 | sram256 | **64KB** A15 bank |
| **Clock (4 MHz → 2 MHz)** |
| 20 | Osc | *(4 MHz half-can)* | Crystal oscillator 4.000 MHz | 1 | HC-49 half | TH | clock | 마스터 클록 |
| 21 | IC | 74HC74 | Dual D flip-flop | 1 | DIP-14 | TH | clock | ÷2 → 2 MHz, 50% duty |
| 22 | IC | 74HC04 | Hex inverter | 1 | DIP-14 | TH | clock | clk buffer / complement |
| 23 | IC | 74HC14 | Hex Schmitt inverter | 2 | DIP-14 | TH | clock | clk tree, edge sharpen · **M7** |
| **Level shift (optional lab)** |
| 24 | IC | SN74LVC8T245DWR | 8-bit dual-supply transceiver | 3 | SOIC-24 | SMD→#3 | — | 3.3 V ↔ 5 V (Nano·Flash·CPLD) |
| **Power · programming** |
| 25 | Module | PWR080015 | Breadboard 5 V / 3.3 V supply | 1 | module | TH | BB | 듀얼 레일 |
| 26 | Cable | SZH-CAB28 | Micro-B USB 1 m | 1 | — | — | BB | Nano / module power |
| 27 | Module | THC-NAO002 | Arduino Nano V3 CH340 (C-type) | 1 | module | TH | BB | Flash CW bit-bang |
| 28 | IC | 74HC595 | 8-bit shift register | 3 | DIP-16 | TH | — | Flash program addr ext |
| **Passives · integrity** |
| 29 | Cap | *(Mono 0.1 µF Y5V 50 V)* | Decoupling 0.1 µF | 34 | radial | TH | BB | 1:1 per IC +4 @ CPLD |
| 30 | Cap | *(Dip tantal 10 µF 35 V)* | Bulk decoupling 10 µF | 10 | radial | TH | BB | VCC rail |
| 31 | Cap | *(E/C 63 V 10 µF 105 °C 5×11)* | Electrolytic 10 µF | 10 | radial | TH | BB | ripple / POR |
| 32 | Bead | BMI-BEAD-3590L | Ferrite bead | 10 | axial | TH | BB | power filtering |
| 33 | Res array | *(8×330 Ω SIP)* | Bus series termination 33 Ω ×8 | 10 | SIP-9 | TH | BB | data bus |
| 34 | Res array | Bourns 4708-103-103LF | 8×10 kΩ isolated SIP | 10 | SIP-9 | TH | BB | bus pull-up |
| 35 | Res | *(1/4 W 103F 10 kΩ 1%)* | Axial resistor 10 kΩ | 10 | axial | TH | BB | pull-up / RC |
| 36 | Diode | 1N4148 | Switching diode | 10 | DO-35 | TH | BB | POR / clamp |

**§1 합계 (라인):** 37 · **74HC DIP:** 38 pcs · **SMD:** Flash×1, SRAM×2, LVC245×3, CPLD×1

---

## §2 v0.1 vs v1.3 — BOM Δ

| MPN | v0.1 | v1.3 | 비고 |
|-----|------|------|------|
| 74HC574 | **7** | 3 | +4 GPR |
| SST39SF010A | **1** | 2 | single NOR |
| IS62C256AL | **2** | 1 | 64 KB |
| 74HC138 | **0** | 1 | decode → CPLD |
| MAP_MODE DIP | **1** | — | Boot/Run |
| ATF1504AS role | system_ctrl | regfile | |

---

## §3 Package · SMT / 실장

| MPN | Vendor package | Footprint / 실장 |
|-----|----------------|------------------|
| 74HC* (DIP rows) | DIP | 2.54 mm breadboard direct |
| ATF1504AS-10JU44 | PLCC-44 | Row #15 adapter → breadboard |
| SST39SF010A-70-4C-PHE | TSOP-32 (4C-PHE) | Row #3 adapter; verify pin 1 |
| IS62C256AL-45ULI-TR | SOP-28 | Row #3 adapter |
| SN74LVC8T245DWR | SOIC-24 (DWR) | Row #3 adapter |
| OSC 4 MHz half-can | HC-49S half | Row #20; short leads to #21–23 |

---

## §4 BOM에 포함하지 않음

| Item | Note |
|------|------|
| JTAG ISP | CPLD synthesis |
| RP2350B coprocessor | 별도 보드 — [rp2350-coprocessor.md](docs/rp2350-coprocessor.md) |
| alu8_decode PLA | hwsim only — **8b Flash CW** direct |

---

## §5 미주문 · 수량 부족 (v1.3 기준)

[디바이스마트 1차 주문](docs/purchase-devicesmart.md) 대비 **추가 발주** 필요:

| MPN | BOM Qty | Ordered | Δ |
|-----|---------|---------|---|
| ATF1504AS-10JU44 | 1 | 0 | **+1** |
| PLCC-44→DIP-44 adapter | 1 | 0 | **+1** |
| 74HC14 (DIP) | 2 | 0 | **+2** |
| 74HC86 (DIP) | 4 | 2 | **+2** |
| 74HC157 (DIP) | 8 | 5 | **+3** |
| 74HC04 (DIP) | 3 | 1 | **+2** |
| Mono 0.1 µF | 34 | 30 | **+4** |

*574×7, 161×4, 245×2 등은 1차 주문 **재고 여유**.*

---

## §6 설계 집계 (참고 — §1과 불일치 시 §1 우선)

| Block | 74HC count | Key MPN |
|-------|------------|---------|
| ALU | 20 | 283×2, 153×4, 86×4, 08×2, 32×2, 157×6, 04×2 |
| CPU | 12 | 574×7, 161×3, 157×2 |
| Bus | 1 | 245×1 |
| Clock | 4 IC + osc | 74×1, 04×1, 14×2 |
| CPLD | 1 | ATF1504AS system_ctrl |
| Memory | 3 | SST39×1, IS62×2 |

---

## §7 구매 단계 (마일스톤)

| 단계 | 내용 | BOM rows |
|------|------|----------|
| ① | ALU B3 | 4–10 |
| ② | v1.3 CPU + CPLD | 11–15, 16–19 |
| ②b | v1.2 fallback | +574×1, +157×4 (§2) |
| ③ | Clock M7 + decap | 20–23, +4× #29 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-01 | **v0.1** — 574×7, SST39×1, IS62×2, system CPLD |
| 2026-06-01 | 메모리 풀 품번 복원 |
| 2026-05-31 | v1.3 CPLD hybrid 권장 |
| 2026-05-29 | 초기 BOM (git `dbb6e8c`) |
