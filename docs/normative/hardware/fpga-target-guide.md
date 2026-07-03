# Plover v1.0 — FPGA 타깃 가이드 (기준 문서)

**Version:** 0.1 · **Date:** 2026-06-02  
**Status:** Planning — normative for **future FPGA / Verilog** work; **not** the active breadboard/PCB build path  
**Audience:** 교육용 FPGA 보드 사용자, 원칙·외부 ROM/RAM·주변 분리 구현자, 향후 RTL 제공·프로젝트 확장 담당자

**Related (TTL 실기):** [system-architecture.md](system-architecture.md) · [BOM.md](../../../BOM.md) (5 V) · [BOM-3v3.md](../../../BOM-3v3.md) (3.3 V PCB)  
**Related (명세):** [microcode-spec.md](microcode-spec.md) · [memory-map.md](memory-map.md)  
**개발자 검증:** [developer/verification-gates.md](../../developer/verification-gates.md)

---

## 1. 목적과 범위

### 1.1 이 문서가 하는 일

| 항목 | 내용 |
|------|------|
| **정리** | v1.0 CPU를 **5 V 빵판 / 3.3 V PCB가 아닌 FPGA**에 올릴 때의 리소스·메모리·속도·비용 고찰 |
| **기준** | 이후 공개할 **Verilog (또는 SystemVerilog) RTL** 의 아키텍처·검증·메모리 맵 **단일 참조** |
| **분기** | **원칩 FPGA**, **FPGA + 외부 ROM/RAM**, **FPGA + 외부 주변(RP2350 등)** 구성을 명시적으로 구분 |

### 1.2 이 문서가 하지 않는 일

- Quartus/Vivado 프로젝트 파일·핀 배치·타이밍 제약 **제공** (RTL 마일스톤 이후)
- TTL BOM과 **핀·전기 1:1** 대응 보장 (3.3 V FPGA 구현은 [BOM-3v3.md](../BOM-3v3.md) 정합이지 [BOM.md](../BOM.md) 5 V 버스와 동일하지 않음)
- **합성 완료 RTL** — 저장소에 **아직 없음** (§8 로드맵)

FPGA RTL 정합성은 [microcode-spec.md](microcode-spec.md) · `hw/fixtures/` · breadboard bring-up 체크리스트를 기준으로 한다. 사전 시뮬·회귀는 [developer/verification-gates.md](../../developer/verification-gates.md).

### 1.4 레거시 Verilog

[archive/verilog-sim/rtl/](../archive/verilog-sim/rtl/) 는 **구세대**(16b CW·Flash×2 등) 이다. v1.0 FPGA RTL은 **이 가이드 + v1.0 명세**를 따르며, 아카이브는 참고용으로만 사용한다.

---

## 2. v1.0 하드웨어 요약 (FPGA에 매핑할 블록)

```
                    ┌── system decode (CPLD → RTL comb) ──┐
  clk (2 MHz 목표)  │ MAP_MODE · CS · LOAD_R* · MMIO    │
                    └───┬──────┬──────┬─────────────────┘
                        │      │      │
                   GPR×4   RAM 64KB   NOR 128KB (또는 동등)
                   alu8    (A15)     boot + CW @ $4000
                        │      │      │
                        └──────┴──────┴── PC/MBR/phase FSM
```

| 블록 | TTL v1.0 | FPGA 권장 매핑 |
|------|----------|----------------|
| **alu8** | 74HC **24** IC (TTL) | 단일 **8b ALU** 모듈 (12 opcode + 병렬 CMP, [alu-opcodes-timing.md](alu-opcodes-timing.md)) |
| **GPR** | 574×4 | 레지스터 파일 **32 bit** + MBR/PCH/flags |
| **system_ctrl** | ATF1504AS ≤64 MC | **조합** decode (상태 레지스터 없음, [cpld-system-controller.md](cpld-system-controller.md)) |
| **CW** | SST39 @ `$4000` + `{opcode,phase}` | **BRAM** 또는 외부 SPI/병렬 Flash |
| **RAM** | 2× IS62C256 | **BRAM**, **SDRAM**(교육 보드), 또는 **외부 SRAM** |
| **Mailbox** | `$FF00–$FFFB` | FPGA 내부 레지스터 또는 **RP2350** GPIO/버스 |
| **Copro** | RP2350B | FPGA **밖** (권장) |

명세 클록: **4 MHz ÷ 2 = 2.0 MHz** ([system-architecture.md](system-architecture.md)). FPGA에서는 **2 MHz로 맞추거나**, 검증 후 **더 높은 `clk_sys`** 를 쓸 수 있다 (§6).

---

## 3. 배치 모델 (세 가지)

### 3.1 모델 A — 원칙 FPGA (로직 + RAM + ROM 온칩)

| 리소스 | 추정 (행위적 RTL, 합성 전) |
|--------|---------------------------|
| **LUT/LE** | 2 500 – 4 500 (구조 복제 시 상한) |
| **FF** | 500 – 900 |
| **온칩 RAM** | 프로그램 **64 KB** + Flash 이미지 **최대 128 KB** → **~1.5 Mbit** BRAM |

**적합 디바이스 클래스 (참고):** AMD Spartan-7 **XC7S25**, Lattice **ECP5 LFE5U-25F**, Intel **MAX 10 10M25** — BRAM 용량이 지배.

**한계:** 소형 FPGA(iCE40 UP5K, MachXO2 2K 등)는 **온칩 RAM 용량**으로 **모델 A 불가**.

### 3.2 모델 B — FPGA + 외부 ROM & RAM (v1.0 BOM과 개념 동일)

| FPGA에 남는 것 | 외부로 분리 |
|----------------|-------------|
| ALU, GPR, decode, µphase FSM | **IS62C256×2** (64 KB) 또는 **SDRAM** |
| (선택) CW 캐시·Mailbox | **SST39SF010** (128 KB NOR) |

| 리소스 | 추정 |
|--------|------|
| **LUT/LE** | 2 000 – 3 500 |
| **BRAM** | 수 Kbit – 수십 Kbit (CW 64×8, Mailbox, 부트 스텁) |

**적합 클래스:** **EP4CE6**, **ECP5-12F/25F**, **XC7S15**, **iCE40 HX8K**, **MAX 10 10M08** 등.

**Plover 프로토 권장:** 실기 BOM과 **검증 스토리**를 맞추기 쉬운 구성. 교육 보드는 흔히 **병렬 SRAM 대신 SDRAM**을 탑재한다 (§5).

### 3.3 모델 C — FPGA(CPU) + 외부 메모리 + 외부 주변

| 항목 | 내용 |
|------|------|
| **CPU 코어** | 모델 B와 동일 |
| **RP2350** | VDU, HID, vFDD — [mailbox-protocol.md](../copro/mailbox-protocol.md) |
| **절감** | 5 V↔3.3 V **LVC245** 다수, vFDD 버퍼 FSM → **~150–400 LUT** (전체의 **~5–15%**) |

Mailbox **252 B**를 RP2350 SRAM에 두면 FPGA BRAM을 추가 절약할 수 있다.

---

## 4. 리소스·가격 (계획용, 2026-06 기준)

> **주의:** 칩 단가는 유통사·패키지·수량·재고에 따라 변동한다. **LCSC 1 pcs** 는 **프로토 1장** 기준, **100+** 는 소량 할인 감각이다. 한국 직구 시 **환율·관세·배송** 별도.

### 4.1 칩 단가 (USD, 참고)

| 클래스 | 대표 MPN | 1 pcs (참고) | 100 pcs (참고) | 모델 |
|--------|----------|--------------|----------------|------|
| Spartan-7 25K | XC7S25-1CSGA225I | ~16 | ~13 | A |
| ECP5 25K | LFE5U-25F-7BG256I | ~12 | ~9 | A, B |
| Spartan-7 15K | XC7S15-2FTGB196I | ~19 | ~15 | B |
| ECP5 12K | LFE5U-12F-6BG256C | ~6–9 | ~3–8 | B |
| Cyclone IV 6K | EP4CE6E22C8N | (보드 번들) | — | B |
| MAX 10 25K / 8K | 10M25 / 10M08 | ~25–48 / ~8–25 | 편차 큼 | A / B |
| iCE40 UP5K | ICE40UP5K-SG48I | ~8 | ~6 | C (로직만) |

**결론 (비용):** **수백 USD급 개발 보드/FPGA는 필수 아님.** 모델 B/C는 **칩 $8–20 + 외부 SRAM/NOR $10–15** 수준에서 프로토 가능.

### 4.2 교육 보드 (EP4CE6 + USB Blaster, ~$19–50)

| 항목 | 전형 사양 |
|------|-----------|
| FPGA | **EP4CE6** — 6 272 LE, **270 Kbit** M9K (~33 KB), PLL×2 |
| 온보드 RAM | **64 Mbit SDRAM** (8 MB) — Nios 데모용; **IS62 병렬 SRAM 아님** |
| 설정 | **EPCS16** (SPI) |
| 클록 | **50 MHz** |
| 툴 | **Quartus Prime Lite** (Cyclone IV 무료) |

**구매 시 확인:** SDRAM·EPCS16·**USB Blaster 포함** 여부; 최저가는 **코어보드만**인 경우 있음.

**Waveshare CoreEP4CE6** (~$39) 등은 **SDRAM 없음** — 모델 B 시 외부 메모리 필수.

---

## 5. 교육 보드 (EP4CE6) — Plover에 쓸 때

### 5.1 가능한 것

| 단계 | 내용 |
|------|------|
| 1 | ALU + GPR + phase FSM (LED/스위치) |
| 2 | CW 테이블 in **BRAM** — `cw.hex` / [pack_control_store.py](../tools/pack_control_store.py) |
| 3 | **SDRAM 컨트롤러**로 64 KB 논리 맵 + 프로그램 로드 |
| 4 | (선택) GPIO Mailbox + **RP2350** — LDIO/STIO |

### 5.2 TTL/BOM과 다른 점

| TTL v1.0 | EP4CE6 보드 |
|----------|-------------|
| 병렬 SST39 + IS62 | **SDRAM + EPCS** |
| 2 MHz 시스템 | **50 MHz** 오실레이터 (내부 분주 가능) |
| 5 V ([BOM.md](../../../BOM.md)) | **3.3 V** ([BOM-3v3.md](../../../BOM-3v3.md) 정합) |

### 5.3 권장 FPGA 메모리 맵 (SDRAM 보드용 초안)

실기 [memory-map.md](memory-map.md) **논리 주소**는 유지하고, **물리 구현**만 치환한다.

| CPU 범위 | Mode A | Mode B | FPGA 구현 (초안) |
|----------|--------|--------|------------------|
| `$0000–$07FF` | Boot ROM | RAM | SDRAM 또는 EPCS에서 **복사 후 실행** / small boot in BRAM |
| `$0800–$FEFF` | RAM | RAM | **SDRAM** |
| `$FF00–$FFFB` | Mailbox | Mailbox | BRAM 레지스터 또는 RP2350 |
| `$FFFC–$FFFF` | Vector ROM | Vector RAM | SDRAM + `MAP_MODE` |

**CW / microcode:** Flash `$4000` 인덱스는 RTL에서 **`store_index = (opcode<<2)|phase`** 로 **BRAM 64×8** 에 매핑 ([microcode-spec.md](microcode-spec.md) §3).

---

## 6. 속도 (MIPS) — 클록과 구현 방식

**MIPS** = 초당 **매크로 명령**(opcode 1개) 수. v1.0 TTL 목표: [developer/project/roadmap-next.md](../../developer/project/roadmap-next.md).

| 프로파일 @ **2 MHz** | MIPS |
|----------------------|------|
| GPR 루프 | ~0.8 – 1.0 |
| OS mix + MMIO poll | ~0.3 – 0.5 |

### 6.1 구현 방식별 (EP4CE6 @ 50 MHz 보드 기준)

| 방식 | `clk_sys` | 기대 MIPS | 비고 |
|------|-----------|-----------|------|
| **Cycle-accurate micro** (TTL 동일) | **2 MHz** | **~0.3 – 1.0** | 명세 타이밍 스토리와 동일 |
| **Faithful micro + SDRAM** | 50 MHz | **~2 – 8** | random read wait state 지배 |
| **Macro-fast** (micro phase 생략) | 50 MHz | **~5 – 20+** | bring-up·데모용 |

**병목:** EP4CE6 **LE가 아니라 메모리**(SDRAM 첫 read, PC 순차성)와 **MMIO 폴링**.

**6502 @ 1 MHz** 대비: 2 MHz cycle-accurate Plover ≈ **동급~약간 빠른 8비트기**; 50 MHz + 단순화 RTL ≈ **수 배~十数 배** (워크로드 의존).

### 6.2 ALU 타이밍

조합 ALU worst **151 ns @ max** (SUB Y; arith path, [alu-opcodes-timing.md](alu-opcodes-timing.md)) — **2 MHz** (250 ns 반주기) **충분** (slack ~99 ns). Logic opcodes **46 ns** (153 mux1). CMP flags via **comparator** (~65 ns). **50 MHz** (20 ns)에서는 **행위적 단일 사이클 ALU** 가 일반적.

---

## 7. RTL 설계 원칙 (향후 Verilog 제공 기준)

### 7.1 스타일

| 원칙 | 설명 |
|------|------|
| **행위 우선** | 게이트 단위 74HC 복제는 **교육/타이밍 실험**용 옵션; 기본 산출물은 **compact CPU** |
| **명세 동기** | ISA·phase count — [microcode-spec.md](microcode-spec.md) |
| **CW** | `tools/pack_control_store.py` / `hw/fixtures/control/cw.hex` **단일 소스** |
| **Reset** | `$FFFC` 벡터, `MAP_MODE` — [bootloader.md](../boot/bootloader.md) |
| **No IRQ** | 폴링만 — [mailbox-protocol.md](../copro/mailbox-protocol.md) |

### 7.2 구현 등급 (검증 깊이)

| 등급 | 설명 | 검증 |
|------|------|------|
| **L0** | ALU8 단독 | cocotb/iverilog + [alu-opcodes-timing.md](alu-opcodes-timing.md) |
| **L1** | MicroEngine 1 phase = 1 clk | RTL vs 명세 phase table |
| **L2** | Macro + fetch + [memory-map.md](memory-map.md) | hex 프로그램 on-board |
| **L3** | SDRAM/QSPI 메모리 래퍼 | 보드 특화; timing constraints |
| **L4** | Mailbox + RP2350 | 시스템 통합 |

### 7.3 디렉터리 (계획)

```
hw/rtl/v1.0/          # 신규 (미작성) — 이 문서가 normative
  alu8.sv
  regfile.sv
  sys_decode.sv
  micro_sequencer.sv
  mem_arbiter.sv      # BRAM | SDRAM | optional parallel NOR/SRAM
  plover_top.sv
```

레거시: [archive/verilog-sim/rtl/](../archive/verilog-sim/rtl/) — **이식 시 v1.0 10b CW로 재작성**.

### 7.4 메모리 인터페이스 추상화

RTL 상단에서 **백엔드**만 교체할 수 있게 한다.

| Backend | 용도 |
|---------|------|
| `mem_bram` | 시뮬·소형 테스트 |
| `mem_sdram` | EP4CE6 교육 보드 |
| `mem_parallel` | IS62 + SST39 (BOM-3v3 PCB와 공학 샘플) |

버스: **8b data**, **16b addr**, `mem_rd`/`mem_wr` — CW 비트 [microcode-spec.md](microcode-spec.md) §2.

---

## 8. 검증 계획

| 단계 | 산출물 |
|------|--------|
| FSM table | M3a bring-up checklist |
| CW / fixtures | `hw/fixtures/` · breadboard gate |
| RTL sim | (예정) Verilator/Icarus + `hw/fixtures/sram/*.hex` |
| FPGA on-board | (예정) SignalTap / LED — Fib 데모·단일 명령 스텝 |

사전 시뮬·회귀 명령: [developer/verification-gates.md](../../developer/verification-gates.md).

**Parity 목표:** normative ISA에서 **PC·GPR·Z/C·halt** 가 breadboard 관측과 RTL 행위가 일치.

---

## 9. 마일스톤 로드맵 (FPGA 트랙)

| # | 산출물 | 의존 |
|---|--------|------|
| F0 | **이 문서** | — |
| F1 | `hw/rtl/v1.0/alu8` + bench | [alu-opcodes-timing.md](alu-opcodes-timing.md) |
| F2 | micro sequencer + BRAM CW | `cw.hex`, micro tests |
| F3 | Macro engine + BRAM RAM | boot handoff on breadboard |
| F4 | `plover_top` + SDRAM (EP4CE6) | Quartus project template |
| F5 | Mailbox + RP2350 GPIO | [rp2350-coprocessor.md](rp2350-coprocessor.md) |
| F6 | (선택) Parallel NOR/SRAM wrapper | [BOM-3v3.md](../BOM-3v3.md) |

TTL 실기 마일스톤: [implementation-plan-v1.0.md](../../developer/project/implementation-plan-v1.0.md) — **병렬 진행 가능**, 문서만 교차 링크.

---

## 10. 빠른 결정표

| 목표 | 권장 |
|------|------|
| **가장 저렴하게 CPU만 학습** | EP4CE6 kit (~$19) + **모델 B** + SDRAM IP |
| **BOM-3v3와 동일 메모리** | **모델 B** + parallel IS62/SST39 · XC7S15 / ECP5-12F |
| **온칩 64K+128K** | **모델 A** · XC7S25 / ECP5-25F |
| **명세와 동일 타이밍 스토리** | **`clk_sys = 2 MHz`** |
| **Fib/데모 wall-clock** | 50 MHz + **L2 macro-fast** (명세 micro와 별도 문서화) |

---

## 11. 변경 이력

| Date | Note |
|------|------|
| 2026-06-02 | 초판 — FPGA 리소스·EP4CE6·속도·RTL 기준·로드맵 (대화 고찰 정리) |
