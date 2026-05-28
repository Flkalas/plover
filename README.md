# Plover

**Plover**는 74HC 시리즈 디스크리트 로직으로 구현하는 8비트 **VLIW-RISC** 홈브류 CPU 프로젝트입니다.  

---

## 한 줄 요약

| 항목 | 내용 |
|------|------|
| 데이터 경로 | 8비트 |
| 제어 방식 | 16비트 VLIW 수평 마이크로코드 (명령어 디코더 없음) |
| 실행 모델 | 1사이클 = 1명령 (파이프라인 없음 또는 1단) |
| 목표 클록 | 4 MHz 마스터 → **2.0 MHz** 시스템 클록 |
| 목표 성능 | **~2.0 MIPS** (0-wait, CPI ≈ 1 가정) |
| 핵심 IC | **42개** (프로그래밍용 74HC595 3개 제외 시 연산·제어·메모리) |
| 구현 형태 | 브레드보드 프로토타입 |

---

## 아키텍처 개요

### VLIW 마이크로코드

`SST39SF010A`(128K×8) **2개를 병렬**로 묶어 **16비트 제어 워드**를 매 클록 출력합니다. 전통적인 opcode 디코더 대신, ROM 비트 필드가 ALU·레지스터·버스·분기 제어선에 **직접** 연결되는 수평 마이크로프로그래밍 구조입니다.

제안된 16비트 필드 예시 (설계 초안):

| 필드 | 비트 | 역할 |
|------|------|------|
| ALU Select | 4 | 산술/논리 연산 선택 |
| Register Sel | 4 | 74HC574 뱅크 입출력 |
| Bus Control | 4 | 74HC157/245 방향·선택 |
| Branch / Misc | 4 | PC(74HC161), MMIO(74HC138) |

실사용 opcode는 하드웨어 fan-out·배선 물리량을 고려해 **32~64개** 수준으로 잡는 것이 현실적입니다.

### 데이터 패스

```
[PC: 74HC161×4] → [병렬 Flash ROM ×2] → 16비트 제어 워드
                              ↓
        ┌─────────────────────┴─────────────────────┐
        │  ALU: 283×2(8b 가산) + 86/08/32 + 153×4   │
        │  레지스터: 74HC574×7                     │
        │  버스: 157 / 245 / LVC8T245(3.3V I/O)    │
        └─────────────────────┬─────────────────────┘
                              ↓
              [SRAM IS62C256 32KB]  [MMIO: 74HC138]
```

- **74HC283×2**: 하위 4비트 `C_out` → 상위 4비트 `C_in` 캐스케이드로 8비트 가산/감산(2의 보수는 74HC86으로 B 반전).
- **74HC574×7**: SRAM 대신 전용 레지스터 — 1사이클 read/modify/write와 글리치 차단용 래치.
- **74HC161×4**: 16비트 프로그램 카운터.
- **IS62C256**: 공유 데이터 SRAM (45 ns). 코프로세서·페이징 등 확장 여지를 둔 설계.

### 클록

| 구성 | 부품 | 역할 |
|------|------|------|
| 마스터 | OSC 4 MHz | 기준 클록 |
| 분주 | 74HC74 | **2.0 MHz**, 50% 듀티 |
| 위상/지연 | 74HC04 | 2상 클록·지연선·버퍼 |

### 계획된 주변·그래픽

- **RP2350B**: 그래픽·I/O 코프로세서 (PIO, 로컬 메모리).
- **Apple II식 인터리브**: CPU와 비디오/주변 로직이 SRAM 접근을 시분할 — CPU가 2 MHz 전 구간을 연산에 쓸 수 있게 하는 설계 목표.
- **SN74LVC8T245×3**: 5 V CPU 도메인 ↔ 3.3 V 코프로세서 버스

---

## 명령·연산 (설계 목표)

### 기본 ISA (하드웨어 직접)

| 유형 | 예시 | 구현 |
|------|------|------|
| 산술 | ADD, SUB | 283 + 86 |
| 논리 | AND, OR, XOR, NOT | 08, 32, 86 |
| 데이터 이동 | MOV, LOAD, STORE | 574, 245, 157 |
| 제어 | JMP, BEQ, BNE | 161, 138 |

곱셈기는 없음. 곱셈·시프트·비교는 **마이크로코드 루틴**으로 처리합니다.

### 의사 연산 예상 사이클 (2 MHz 기준)

| 기능 | 방식 | 예상 사이클 |
|------|------|-------------|
| Shift / Rotate | 153 + 배선 | 1 |
| Compare | SUB + Zero 플래그 | 1 |
| 16비트 ADD/ADC | 하위 8b → 상위 8b + 캐리 | 2 |
| 8비트 곱셈 | Shift-and-add 루틴 | 8~16 |

16비트 연산은 8비트 ALU 2단 + 플래그 레지스터(캐리 보존)로 **2사이클** 마이크로시퀀스로 확장.

---

## 부품 (BOM)

**전체 목록·단가·용도**: [`BOM.md`](BOM.md) (32라인, 핵심 IC 42개, 견적 합계 ~68,295 KRW).

### 핵심 IC 42개 요약

| 분류 | 부품 | 수량 | 비고 |
|------|------|------|------|
| ALU | 74HC283N, 153, 86, 08, 32 | 12 | 8비트 연산·MUX |
| 레지스터/카운터 | 74HC161, 574 | 11 | PC, 누산/래치 |
| 버스 | 74HC157, 245, SN74LVC8T245 | 10 | 중재·레벨 시프트 |
| 디코드 | 74HC138 | 1 | CS / MMIO |
| 메모리 | SST39SF010A, IS62C256 | 3 | VLIW ROM + SRAM |
| 클록 | 74HC74, 74HC04, OSC 4M | 3 | 2 MHz 생성 |
| 프로그래밍 | 74HC595 | 3 | Flash 프로그래머 확장 |

그 외 [`BOM.md`](BOM.md): 브레드보드×4, 전원 모듈·어댑터, 디커플링·종단·풀업, 아두이노 나노.

**기가트론**(TTL 홈브류 ~25–30 IC)보다 칩 수는 많지만, VLIW 직접 제어·레지스터 뱅크·버스 중재·코프로세서 인터페이스를 위해 의도적으로 확장한 규모입니다.

---

## 성능·비교 (설계 가정)

| 시스템 | CPU | 클록 | 체감 MIPS급 | 비고 |
|--------|-----|------|-------------|------|
| **Plover (목표)** | Custom 8b VLIW-RISC | 2.0 MHz | ~2.0 | CPI≈1, 0-wait 목표 |
| Apple I/II | MOS 6502 | ~1 MHz | ~0.5 | CISC, 다사이클 명령 |
| C64 | MOS 6510 | ~1 MHz | ~0.4–0.5 | VIC-II 병목 |
| Commander X16 | WDC 65C02 | 8 MHz | ~4–5 | 고클록 6502 |
| Amiga 500 | MC68000 | 7.09 MHz | ~1.5–2 | 16/32b, 블리터 |

- **6502 대비**: 클록 2배 × CPI 1/2~1/7 → 정수 루프에서 이론상 큰 이득. 다만 **코드 밀도**는 RISC/VLIW가 불리할 수 있음.

## 구현·검증 로드맵 (문서 기준)

1. **클록 + PC** — 4 MHz → 2 MHz 분주, ROM 주소 순차 접근 확인  
2. **버스 + SRAM** — 157/245 중재, 읽기/쓰기 타이밍  
3. **ALU + 574** — 1사이클 연산 경로, 캐리 전파·셋업 타임  
4. **마이크로코드** — 아두이노 + 595로 SST39SF010A 프로그래밍  
5. **코프로세서** — LVC8T245 경로, RP2350B 그래픽 통합  
6. **인터리브** — Apple II식 φ₀/φ₁ 메모리 슬롯 (선택)

---

## 문서

| 파일 | 내용 |
|------|------|
| [`BOM.md`](BOM.md) | 부품 목록(BOM) — 단가·용도·42 IC 분류 |
| [`docs/README.md`](docs/README.md) | 문서 인덱스 |
| [`docs/microcode-spec.md`](docs/microcode-spec.md) | 16비트 VLIW 제어 워드·시뮬 ISA |
| [`rtl/README.md`](rtl/README.md) | Verilog RTL 개요 (ALU·레지스터·코어) |
| [`rtl/alu/README.md`](rtl/alu/README.md) | ALU — 283 구조 / 153·게이트 단순화 설명 |
| [`sim/README.md`](sim/README.md) | 테스트벤치·ROM hex |
| [`tools/README.md`](tools/README.md) | `microasm`, `pack_rom` |
| [`lib/README.md`](lib/README.md) | 예제 `.micro` |
| [`sim-runner/README.md`](sim-runner/README.md) | FastAPI 시뮬 API |
| [`web/README.md`](web/README.md) | React UI |

---

## Verilog 시뮬레이터

브레드보드 조립 전에 **Icarus Verilog**로 RTL을 검증하고, 웹 UI에서 ALU·코어·마이크로코드를 실행할 수 있습니다. ALU는 **74HC283 캐스케이드만 구조 모듈**이고, 153/86/08/32는 행위 수준으로 단순화되어 있습니다 — 상세는 [`rtl/alu/README.md`](rtl/alu/README.md).

### 요구 사항

- [Icarus Verilog](http://iverilog.icarus.com/) (`iverilog`, `vvp`) — Linux: `sudo apt install iverilog`, Windows: MSYS2/Chocolatey 또는 **WSL2 권장**
- Python 3.10+
- Node.js 18+ (웹 UI)

### WSL2에서 실행 (Windows에 WSL이 있을 때)

저장소가 `D:\Github\plover`에 있으면 WSL 경로는 `/mnt/d/Github/plover`입니다.

**1) WSL 터미널 열기** — PowerShell에서 `wsl` 또는 “Ubuntu” 앱.

**2) 패키지 한 번 설치 (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install -y iverilog make python3 python3-pip python3-venv
# 웹 UI까지 쓸 때
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**3) 프로젝트로 이동 후 RTL만 검증**

```bash
cd /mnt/d/Github/plover
make test
```

**4) 시뮬 API + 웹 (터미널 2개, 둘 다 WSL에서)**

```bash
# 터미널 A
cd /mnt/d/Github/plover
python3 -m venv .venv && source .venv/bin/activate
pip install -r sim-runner/requirements.txt
make sim-server
```

```bash
# 터미널 B
cd /mnt/d/Github/plover/web
npm install
npm run dev
```

Windows 브라우저에서 [http://127.0.0.1:5173](http://127.0.0.1:5173) 접속. Vite가 `/api`를 `127.0.0.1:8000`으로 프록시하므로 **sim-server도 WSL에서 띄운 경우** 그대로 동작합니다.

**참고**

| 항목 | 설명 |
|------|------|
| 경로 | `/mnt/d/...`는 Windows `D:\`와 같은 파일. Windows·WSL 어느 쪽에서 편집해도 됨. |
| `make`만 | RTL·ROM 검증은 **Node 없이** `make test` / `make rom`만으로 가능. |
| Git 줄바꿈 | `git config core.autocrlf input` (WSL) 권장 — `.micro`/`Makefile` CRLF 이슈 방지. |
| 느린 I/O | `/mnt/d`가 느리면 `~/plover`에 `git clone` 후 WSL 내부에서 작업하는 편이 빠름. |

### 빠른 시작

```bash
# RTL 테스트 (ALU + 코어)
make test

# 마이크로코드 → sim/rom_*.hex
make rom
python3 tools/microasm.py lib/inc_r1.micro -o sim

# 시뮬 API + 웹 UI (터미널 2개)
make sim-server    # http://127.0.0.1:8000
make web-dev       # http://127.0.0.1:5173
```

### 디렉터리

| 경로 | 설명 |
|------|------|
| `rtl/` | 74HC 행위 모델 + `plover_core` |
| `sim/` | 테스트벤치, ROM hex |
| `tools/microasm.py` | 마이크로어셈블러 |
| `lib/*.micro` | 예제 마이크로 프로그램 |
| `sim-runner/` | FastAPI → iverilog |
| `web/` | React 시뮬 UI |

---

## 상태

- [x] 아키텍처·BOM 설계 (대화로 정리)
- [x] 부품 주문
- [ ] 브레드보드 조립·클록/PC 검증
- [x] 마이크로코드·어셈블러/툴체인 (시뮬 MVP)
- [x] Verilog 시뮬레이터 (ALU + 코어 + 웹 UI)
- [ ] RP2350B 그래픽 서브시스템

---

## 라이선스

미정. 저장소에 라이선스 파일이 추가되면 이 절을 갱신합니다.
