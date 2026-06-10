# Plover — 구매 목록 (v1.0 breadboard, 1세트)

**Normative:** [docs/hardware/system-architecture.md](docs/hardware/system-architecture.md) v1.0  
**1세트 부품 명세** · 5 V · 74HC DIP 빵판 · **CPLD GPR ~40 MC + 138×2 + 10b CW**  
PCB 3.3 V 대응 목록: [BOM-3v3.md](BOM-3v3.md) (**중복 주문 금지**)  
이력 · 검산 · 발주 기록: [docs/project/bom-maintenance.md](docs/project/bom-maintenance.md)

**구분** · **MPN** · **Qty** · **역할 · 목적** (보드 기능) · **비고** (구매·합산)

| 구분 | # | MPN | Description | Qty | 역할 · 목적 | 비고 |
|------|---|-----|-------------|-----|-------------|------|
| 인프라 · 배선 | 1 | SZH-BBAD-002 | Breadboard 830-pin MB-102 | 4 | CPU·ALU·메모리·CPLD를 나란히 올릴 작업 면 | |
| 인프라 · 배선 | 2 | *(0.6 mm solid wire)* | 3-color jumper wire 1 m | 6 | 전원·점퍼·버스 물리 배선 | |
| 인프라 · 배선 | 3a | *(SOP28/SSOP28 dual)* | SOP28↔DIP adapter | 2 | SOP SRAM을 빵판 DIP에 꽂기 | #19 |
| 인프라 · 배선 | 3b | *(TSOP-32→DIP)* | TSOP-32↔DIP adapter | 0–1 | TSOP Flash를 빵판에 꽂기 | PDIP Flash면 생략 |
| 인프라 · 배선 | 3c | *(SOIC-24→DIP)* | SOIC-24↔DIP adapter | 3 | SOIC 레벨시프터를 빵판에 꽂기 | #24 |
| ALU | 4 | 74HC283N | 4-bit binary full adder | 2 | 8비트 덧셈·뺄셈·증감 연산 | |
| ALU | 5 | 74HC153 | Dual 4-to-1 line data selector/multiplexer | 8 | B 피연산자 경로 선택 + 논리 연산 결과 선택 | |
| ALU | 6 | 74HC157 | Quad 2-line to 1-line data selector/multiplexer | 2 | 산술 결과와 논리 결과 중 ALU 출력 선택 | |
| ALU | 7 | 74HC04 | Hex inverter | 2 | B 피연산자 부호·논리 반전 | |
| CPU · 주소 | 11 | 74HC574 | Octal D-type flip-flop, 3-state | **5** | PC/MBR/**CW_L/CW_H**/FLG | 10b CW = +1 vs 8b |
| CPU · 주소 | 11a | 74HC138N | 3-to-8 line decoder | **2** | CE half-select + coarse map (**×1 보유, +1 주문**) | |
| CPU · 주소 | 11b | 74HC08 / 74HC32 | AND / OR | 2 each | CE glue + mailbox/MAP + BEQ | |
| CPU · 주소 | 12 | 74HC161 | 4-bit synchronous binary counter | 3 | PC 하위·명령 실행 단계(phase) 카운트 | |
| CPU · 주소 | 13 | 74HC157 | Quad 2-line to 1-line data selector/multiplexer | 2 | 주소 버스 하위 8비트 선택 | #6과 합산 4 |
| CPLD · 스위치 | 14 | ATF1504AS (100-TQFP) | CPLD, 64 MC — **GPR only ~40 MC** | 1 | R0–R3 FF; Reg_Sel from CW | PLCC-44 보유 → TQFP 권장 |
| CPLD · 스위치 | 15 | *(TQFP-100 breakout)* | ATF1504 0.5 mm → 2.54 mm | 1 | CPLD 빵판 장착 | |
| CPLD · 스위치 | 16 | *(1C2P slide or DIP-1)* | Single-pole 2-position switch | 1 | Boot/Run MAP_MODE | |
| 버스 · 메모리 | 17 | 74HC245 | Octal bus transceiver | 1 | SRAM 데이터 버스 ↔ CPU 버스 레지스터 | |
| 버스 · 메모리 | 18 | SST39SF010A-70-4C-PHE | 128K×8 parallel NOR Flash | 1 | 부트·10b CW·유틸리티 | |
| 버스 · 메모리 | 19 | IS62C256AL-45ULI-TR | 32K×8 static RAM | 2 | 실행 RAM 64 KB | |
| 클록 | 20 | *(4 MHz half-can osc)* | Crystal oscillator, 4.000 MHz, HC-49 half | 1 | 마스터 클록 | |
| 클록 | 21 | 74HC74 | Dual D-type flip-flop | 1 | 4 MHz → 2 MHz 분주 | |
| 클록 | 22 | 74HC04 | Hex inverter | 1 | 클록 버퍼·극성 반전 | #7과 합산 **3** |
| 클록 | 23 | 74HC14 | Hex Schmitt-trigger inverter | 2 | 클록 배포·완만한 입력 정형 | |
| 레벨 시프트 | 24 | SN74LVC8T245DWR | 8-bit dual-supply bus transceiver, SOIC-24 | 3 | 5 V ↔ 3.3 V | #3c |
| 전원 · 프로그래밍 | 25 | PWR080015 | Breadboard power supply module, 5 V / 3.3 V | 1 | 빵판 전원 | |
| 전원 · 프로그래밍 | 26 | SZH-CAB28 | USB Micro-B cable, 1 m | 1 | Nano USB | |
| 전원 · 프로그래밍 | 27 | THC-NAO002 | Arduino Nano V3.0 compatible, CH340, USB-C | 1 | Flash 비트뱅 | |
| 전원 · 프로그래밍 | 28 | 74HC595 | 8-bit serial-in parallel-out shift register | 3 | Flash 프로그래밍 주소 확장 | |
| 패시브 | 29 | *(Mono 0.1 µF Y5V 50 V)* | Ceramic capacitor, 0.1 µF | 38 | IC 디커플 | +6 여유 |
| 패시브 | 30 | *(Dip tantal 10 µF 35 V)* | Tantalum capacitor, 10 µF | 10 | 벌크 | |
| 패시브 | 31 | *(E/C 63 V 10 µF 105 °C)* | Aluminum electrolytic, 10 µF | 10 | 리플·RC | |
| 패시브 | 32 | BMI-BEAD-3590L | Ferrite bead | 10 | 전원선 억제 | |
| 패시브 | 33 | *(8×330 Ω SIP)* | Resistor network, 33 Ω ×8, bussed | 10 | 버스 댐핑 | |
| 패시브 | 34 | Bourns 4708-103-103LF | Resistor network, 10 kΩ ×8, bussed | 10 | 풀업 | |
| 패시브 | 35 | *(1/4 W 103F 10 kΩ 1%)* | Resistor, 10 kΩ, axial | 10 | 스위치 풀업 | |
| 패시브 | 36 | 1N4148 | Small-signal switching diode | 10 | 리셋·클록 보호 | |
| 장비 · 스위치 | — | *(ATF1504 JTAG/ISP)* | CPLD programmer | 1 | CPLD 소각 | |
| 장비 · 스위치 | — | *(TACT or pushbutton)* | Momentary switch | 1 | CPU RESET | #35 풀업 |
