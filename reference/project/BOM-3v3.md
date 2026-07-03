# Plover — 구매 목록 (v0.1, 1세트 · 3.3 V PCB)

**1세트 부품 명세** · 단일 **3.3 V** · **PCB SMD**  
5 V 빵판 목록: [BOM.md](BOM.md) (**중복 주문 금지**)  
이력 · 검산 · 74HC↔LVC 대응: [../../archive/MANIFEST.md](../../archive/MANIFEST.md)

**구분** · **#** = [BOM.md](BOM.md) 동일 라인(있을 때) · **Pkg** · **역할 · 목적** · **비고**

| 구분 | # | MPN | Description | Pkg | Qty | 역할 · 목적 | 비고 |
|------|---|-----|-------------|-----|-----|-------------|------|
| PCB · 기구 | 0 | *(Plover v0.1 CPU PCB)* | Bare PCB, 2–4 layer FR4 | — | 1 | 모든 SMD·커넥터 실장 기판 | [BOM.md](BOM.md) #1–4·어댑터 **대체** |
| PCB · 기구 | 0b | *(SMD stencil, 선택)* | Stencil | — | 0–1 | 납땜 보조 | |
| 전원 | P1 | USB-C receptacle (USB 2.0) | SMD | 1 | 외부 5 V USB 전원 입력 | [BOM.md](BOM.md) #25 대체 |
| 전원 | P2 | AP2112K-3.3TRG1 (또는 동급 LDO ≥600 mA) | SOT-23-5 | 1 | 시스템 **3.3 V** 레일 | |
| 전원 | P2b | *(선택)* MP2359 등 buck | SOT-23-6 | 0–1 | 전류·발열 여유 | |
| 전원 | P3 | 10 µF + 22 µF ceramic | 0805 | 6 | LDO 입·출력 벌크 | |
| ALU | 4 | SN74LVC283APWR | 4-bit binary full adder | TSSOP-16 | 2 | 8비트 덧셈·뺄셈·증감 연산 | ↔ #4 |
| ALU | 5 | SN74LVC153APWR | Dual 4-to-1 line data selector/multiplexer | TSSOP-16 | 8 | B 피연산자 경로 선택 + 논리 연산 결과 선택 | ↔ #5 |
| ALU | 6 | SN74LVC157APWR | Quad 2-line to 1-line data selector/multiplexer | TSSOP-16 | 2 | 산술 결과와 논리 결과 중 ALU 출력 선택 | ↔ #6 |
| ALU | 7 | SN74LVC04APWR | Hex inverter | TSSOP-14 | 2 | B 피연산자 부호·논리 반전 | ↔ #7 |
| CPU · 주소 | 11 | SN74LVC574APWR | Octal D-type flip-flop, 3-state | TSSOP-20 | 7 | 버스 레지스터·범용 레지스터·플래그·PC 상위 저장 | ↔ #11 |
| CPU · 주소 | 12 | SN74LVC161APWR | 4-bit synchronous binary counter | TSSOP-16 | 3 | PC 하위·명령 실행 단계(phase) 카운트 | ↔ #12 |
| CPU · 주소 | 13 | SN74LVC157APWR | Quad 2-line to 1-line data selector/multiplexer | TSSOP-16 | 2 | 주소 버스 하위 8비트 선택 | ↔ #13 · #6과 합산 4 |
| CPLD · 스위치 | 14 | ATF1504AS-10JU44 | CPLD, 64 macrocell | PLCC-44 | 1 | ROM/RAM/주변 칩 선택·버스 중재·레지스터 쓰기 디코드 | ↔ #14 |
| CPLD · 스위치 | 15 | *(JTAG 2×5, 1.27 mm)* | Pin header, through-hole | TH | 1 | CPLD 구성 데이터 기록 포트 | ↔ #15 어댑터 **대체** |
| CPLD · 스위치 | 16 | *(SMD slide or tact)* | Single-pole 2-position switch | SMD | 1 | 부팅 시 ROM 맵 / 실행 시 RAM 맵을 운영자가 선택 | ↔ #16 |
| 버스 · 메모리 | 17 | SN74LVC245APWR | Octal bus transceiver | TSSOP-20 | 1 | SRAM 데이터 버스 ↔ CPU 버스 레지스터 | ↔ #17 |
| 버스 · 메모리 | 18 | SST39SF010A-70-4C-PHE | 128K×8 parallel NOR Flash | TSOP-32 | 1 | 부트 펌웨어·제어 마이크로코드·유틸리티 저장 | ↔ #18 · 품번 4C |
| 버스 · 메모리 | 19 | IS62C256AL-45ULI-TR | 32K×8 static RAM | SOP-28 | 2 | 실행 RAM 64 KB (칩 2개, 상위 주소로 뱅크) | ↔ #19 · 품번 AL |
| 클록 | 20 | *(4.000 MHz CMOS XO, 3.3 V)* | Crystal oscillator | 3225 / 5032 | 1 | 마스터 클록 발생 | ↔ #20 · 5 V half-can **아님** |
| 클록 | 21 | SN74LVC74APWR | Dual D-type flip-flop | TSSOP-14 | 1 | 4 MHz → 2 MHz 분주 | ↔ #21 |
| 클록 | 22 | SN74LVC04APWR | Hex inverter | TSSOP-14 | 1 | 클록 버퍼·극성 반전 | ↔ #22 · #7과 합산 **3** |
| 클록 | 23 | SN74LVC14APWR | Hex Schmitt-trigger inverter | TSSOP-14 | 2 | 클록 배포·완만한 입력 정형 | ↔ #23 |
| 전원 · 프로그래밍 | 25 | *(Prog header / USB-C UART)* | Pin header or module | TH / SMD | 1 | NOR Flash 내용 쓰기 | ↔ #27 Nano **대체** |
| 전원 · 프로그래밍 | 26 | *(선택)* Pico / CH340 모듈 소켓 | — | — | 0–1 | 개발용 비트뱅 | ↔ #26 케이블 없음 |
| 전원 · 프로그래밍 | 28 | SN74LVC595APWR | 8-bit serial-in parallel-out shift register | TSSOP-16 | 3 | Flash 프로그래밍 시 주소 비트 확장 | ↔ #28 |
| 패시브 | 29 | 0.1 µF 50 V X7R | Ceramic capacitor | 0603 | 47 | IC 전원 핀 옆 고주파 디커플 | ↔ #29 · [검산](../../archive/MANIFEST.md) |
| 패시브 | 30 | 10 µF 10 V X5R | Ceramic capacitor | 0805 | 12 | IC·모듈 VCC 벌크 안정 | ↔ #30 |
| 패시브 | 31 | 10 µF ceramic 또는 E-C | Capacitor | 0805 / 1206 | 4 | 전원 리플·리셋 RC | ↔ #31 |
| 패시브 | 32 | Ferrite bead ~600 Ω @ 100 MHz | Ferrite bead | 0603 | 8 | 전원선 고주파 억제 | ↔ #32 |
| 패시브 | 33 | 33 Ω 1% | Resistor | 0603 | 40 | 데이터 버스 직렬 댐핑 | ↔ #33 |
| 패시브 | 34 | 10 kΩ 1% | Resistor | 0603 | 40 | 버스·입력 풀업 | ↔ #34 · #35 포함 |
| 패시브 | 36 | 1N4148W | Small-signal switching diode | SOD-123 | 6 | 리셋·클록 보호 클램프 | ↔ #36 |
| 코프로 (선택) | 40 | RP2350B | MCU module or QFN | — | 0–1 | 메일박스·vFDD 코프로세서 | PCB 통합 시 |
| 코프로 (선택) | 41 | 0.1 µF 50 V X7R | Ceramic capacitor | 0603 | 4 | RP2350 전원 디커플 | #40용 |
| 장비 · 스위치 | — | *(ATF1504 JTAG/ISP)* | CPLD programmer | — | 1 | CPLD에 구성 데이터 기록 | |
| 장비 · 스위치 | — | *(TACT or pushbutton)* | Momentary switch | SMD | 1 | CPU 수동 리셋 | 10 kΩ 0603 (#34) |
| 장비 · 스위치 | — | *(SMD 납땜 공구)* | — | — | 1 | Fab 후 조립 | |

*[BOM.md](BOM.md) #24 `LVC8T245`×3 · 빵판·점퍼·어댑터는 본 PCB 목록에 **없음**.*
