# Plover 언어·툴체인 에코시스템 (발췌)

> **출처:** [과거로-간-현대-엔지니어의-한계.md](과거로-간-현대-엔지니어의-한계.md), [8비트-컴퓨터-설계-고려사항.md](8비트-컴퓨터-설계-고려사항.md)  
> **목적:** 두 아카이브 문서에서 **언어·컴파일러·인터프리터·툴체인** 관련 논의만 추출·재구성.  
> **현행 로드맵:** [docs/software-roadmap.md](../../software/software-roadmap.md)

---

## 요약: Forth·Subset C 말고 뭐가 있나?

Plover 프로젝트 맥락에서 언급된 언어·런타임·도구는 아래와 같다.

| 분류 | 이름 | 역할 | Plover에서의 위치 |
|------|------|------|-------------------|
| **타겟 (실행)** | **기계어 / Hex** | 최하위, 부트·디버그 | Phase 1 (Bare Metal) |
| | **Plover Assembly** | ISA 1:1, 드라이버·부트로더 | S1, PL-DOS Stage 1 |
| | **매크로 어셈블리** | 반복 패턴 추상화 | 교육 커리큘럼 Phase 3 |
| | **Forth** | 스택 인터프리터, 최초 OS, DOS 쉘 | S3–S4, S7d 쉘 |
| | **Subset C (C0)** | 커널·FS·로더 | S5–S6, PL-DOS 커널 |
| **호스트 (개발 PC)** | **Python** | `plover_cc` 부트스트랩, 링커 스크립트 | S5 초기 |
| **학습·참고** | **gforth** | Forth 문법·스택 연습 (호스트) | — |
| **검토 후 기각** | **Lua / eLua** | 동적 타입·GC — 8비트 RAM 부족 | 미채택 |
| **교육 대안** | **Tiny BASIC / 자체 BASIC** | 파싱·토큰화 교육용 | C 배제 커리큘럼 Phase 5 |
| **역사·벤치마크** | BASIC, Pascal, PL/M, FORTRAN, COBOL, BDS C, SDCC | 1970–80년대 생태계 비교 | 참고만 |
| **가상 실행층** | **vCPU 바이트코드** | 6502형·16비트 스택 머신 에뮬 | 오파츠/Minimalist RISC 설계안 |
| **현대 개념 (참고)** | SSA IR, LLVM, JVM, WebAssembly | 컴파일러·VM 이론 | 오파츠 스택 논의 |

**실제로 구현·로드맵에 올라간 조합:**  
`Assembly` → `Forth` → `Subset C` → (호스트 `Python`으로 컴파일) → `Forth` 쉘.

---

## 1. 언어 진화 경로 (두 가지 시각)

### 1-A. 교육용 — C 배제 모델

8비트 RISC에서 C의 함수 프롤로그/에필로그가 레지스터를 고갈시킨다는 전제 하에, 호환성보다 **하드웨어에 맞는 추상화 단계**를 따른다.

| 단계 | 언어 | 학습 목표 |
|------|------|-----------|
| Phase 1 | Hex (기계어) | Fetch-Execute, OP Code 직접 입력 |
| Phase 2 | Custom Assembly | 니모닉, 심볼, 라벨 |
| Phase 3 | Macro Assembly | 매크로로 첫 추상화 |
| Phase 4 | **Forth** | 스택 기반 대화형 인터프리터/컴파일러 (4KB 이내) |
| Phase 5 | **Tiny BASIC 등 자체 스크립트** | 재귀 하향 파서, `IF`/`WHILE` |

### 1-B. 프로덕션 — VM OS 스택 (S1–S7)

| ID | 산출물 | 언어 |
|----|--------|------|
| S1 | `plover_asm` | Assembly (호스트 툴) |
| S2 | CALL/RET 규약 | Assembly + ABI |
| S3–S4 | Forth core + OS services | Forth |
| S5 | `plover_cc` | Subset C (Forth-hosted 또는 Python 부트스트랩) |
| S6 | microkernel | Subset C |
| S7 | PL-DOS (vFDD, PLFS, `.PLR`) | C 커널 + **Forth 쉘** |

### 1-C. 하드웨어–소프트웨어 공진화 커리큘럼 (5단계)

| 교육 단계 | 소프트웨어 진화 |
|-----------|-----------------|
| 1. Bare Metal | Hex 수동 매핑 |
| 2. Architecture | 2-pass 어셈블러 |
| 3. Interface | 부트로더 어셈블리, MMIO |
| 4. Abstraction | **C0 서브셋 컴파일러**, **vCPU 바이트코드 인터프리터** |
| 5. OS Kernel | 선점형 스케줄러 (C 또는 Forth 기반 협력형) |

---

## 2. 언어별 상세

### 2.1 Forth

**왜 C보다 8비트에 맞는가**

- 스택 머신 기반 — `crt0` 같은 무거운 런타임 불필요
- 컴파일러·인터프리터 일체 — 한 줄 작성 후 즉시 하드웨어 실행
- 커널이 수 KB — RP2350 RAM에서도 컴파일러 자체 구동 가능
- ISA를 “가상 머신”으로 보고 **단어(Word)**를 쌓는 방식 — 레지스터 할당기·콜링 컨벤션 지옥 회피

**구현 단계 (S3–S4)**

1. **Primitives:** `DUP`, `DROP`, `SWAP`, `+`, `@`, `!` (어셈블리)
2. **Kernel:** `IF`, `ELSE`, `DO`, `LOOP`
3. **Interpreter:** 딕셔너리 검색 + inner interpreter 루프

**역할 분담**

- **Bootstrapper:** 하드웨어 기동, FDD 연결, 입출력 확인
- **최초 OS:** S4까지 Forth가 OS 역할 일부 수행
- **DOS 쉘 (S7d):** C 커널 위의 대화형 사용자 인터페이스 (`dir`, `run`, `type` …)

**한계**

- 복잡한 로직에서 스택 조작 지옥(Stack Manipulation Hell)
- 멀티태스킹·TCB 관리에는 C의 구조적 문법이 유리

---

### 2.2 Subset C (plover_cc)

**정의:** ANSI/ISO C의 **부분집합**. 문법은 C, 기능은 CPU·메모리에 맞게 축소.

**v0.1 지원 (S5)**

- 타입: `int8/16`, `uint8/16`, 16비트 포인터
- 제어: `if`, `while`, 함수, 정수 연산
- 런타임 스텁: `_start`, `_write`, `_read` → Forth OS words
- 예시:

```c
int add(int a, int b) { return a + b; }
int main(void) { return add(2, 3); }
```

**명시적 비지원:** `float`, `struct`(초기), preprocessor, `#include` (단일 파일 우선)

**구현 레이어**

| Layer | 구현 |
|-------|------|
| Lexer/parser | Forth `VOCABULARY C:` 또는 호스트 **Python** `plover_cc` |
| Codegen | AST → `plover_asm` 텍스트 → `.sram.hex` |
| Self-host | `forth/cc/` (S5b 목표) |

**왜 Lua 대신 Subset C인가**

| 항목 | Lua VM | Subset C |
|------|--------|----------|
| 타입 | 동적 (무거움) | 정적 |
| 메모리 | GC 필수 | 수동 (`malloc`/`free`) |
| 실행 | 인터프리팅/JIT | **기계어 직접 실행** |
| 8비트 적합성 | 낮음 (수백 KB) | 높음 |

Lua는 “RAM이 부족해서”가 아니라 **아키텍처와 맞지 않아** 기각. Subset C는 컴파일 결과가 어셈블리와 동일한 명령열이라 **구조적 부하가 거의 없음**.

**C를 꼭 해야 하나?**

- **안 해도 됨:** 하드웨어 원리·자체 기계 구축이 목표면 Forth만으로도 충분
- **하는 이유:** 범용성 검증, OS 커널 가독성, self-hosting 졸업 시험, ABI·TCB 관리
- **권장 태도:** C *사용자*가 아니라 C *컴파일러 구현자*

---

### 2.3 Assembly (Plover Assembly)

- 부트로더, 인터럽트 벡터, Mailbox 프로토콜 — **오버헤드 0%**
- `plover_asm`: 2-pass, labels, ORG
- PL-DOS Stage 1: Boot/Driver 전담

---

### 2.4 Python (호스트 전용)

- `plover_cc/parse.py`, `codegen.py` — 타겟이 아닌 **크로스 컴파일 부트스트랩**
- 초기 링커 역할: 심볼 테이블 관리 스크립트 (`plover_ld` 전 단계)
- GCC/LLVM 포팅 대신 **500~1000줄 Plover-CC** 권장

---

### 2.5 BASIC / Tiny BASIC (교육·참고)

**1970–80년대 주류 (Z80/6502)**

| 언어 | 용도 |
|------|------|
| Assembly | OS 커널, 게임, 부트로더 |
| BASIC | 사용자 앱, 교육 (ROM 내장) |
| Forth | 임베디드·천문 제어 |
| Pascal / PL/M | CP/M 일부 상용 SW |
| C (BDS C 등) | 8비트에선 비주류 — 코드 크기·속도 |

**Plover 교육 대안:** Wozniak식 **Integer BASIC** — 토큰화·파싱 교육에 직관적.

**벤치마크 시스템**

| 시스템 | 주력 언어 |
|--------|-----------|
| RC2014 (Z80) | C, Assembly, BASIC — CP/M |
| Magic-1 | C (Subset), Assembly — Unix-like OS |
| Ben Eater 6502 | Machine Code, Assembly, BASIC — Monitor만 |
| Gigatron | C (Subset), Assembly — Tiny BASIC |

---

### 2.6 Lua (기각)

- 동적 타입 + GC + 자체 바이트코드 VM
- eLua도 8비트 16–32KB RAM에 코어 엔진 적재 불가
- 향후 16/32비트·대용량 RAM 확장 시 **응용 계층** 후보로만 언급

---

### 2.7 vCPU / 바이트코드 (설계안)

오파츠·Minimalist RISC 맥락에서 ISA가 빈약할 때:

- 네이티브 RISC는 I/O·비디오 비트뱅 (10 MHz)
- 사용자 프로그램은 **16비트 vCPU 바이트코드** (6502형 또는 스택 머신) 인터프리트 (~1 MHz 체감)
- **Threaded Code / Forth 커널:** 코드 조밀도 40%+ 개선
- 교육 Phase 4: vCPU 바이트코드 인터프리터 + C0 컴파일러 병행

---

## 3. 컴파일러·툴체인

### 3.1 최소 스택 (범용 asdf 아님)

```
C 소스 → [plover_cc Front/Middle] → Plover Assembly → [plover_asm] → .o / hex
                                                              ↓
                                                    [plover_ld] → plover.bin
```

- **Front-end:** C → AST (Python `lark`/`ply`)
- **Middle-end:** AST → IR (간단 최적화)
- **Back-end:** IR → ISA 명령 (`PUSH`, `LOAD`, …)

### 3.2 크로스 vs 셀프 호스팅

| 방식 | 8비트 RISC | 판정 |
|------|------------|------|
| 크로스 컴파일 (PC → 타겟) | Small C / plover_cc | **가능** |
| 셀프 호스팅 (타겟 위에서 C 컴파일) | 32KB DMEM, 파싱 재귀 | **불가** (초기) |

### 3.3 다언어 혼용 — ABI·링킹

**먼저 정의할 것 (도구보다 우선):**

- 인자: R0, R1, …
- 반환: R0
- 스택: SP 기반 지역 변수

**도구**

| 도구 | 입력 | 출력 |
|------|------|------|
| `plover_asm` | `.s` | `.o` |
| `plover_cc` | `.c` | `.s` |
| `plover_ld` | 여러 `.o` | 단일 hex/bin |

**초기 회피 전략**

- 단일 C 파일 컴파일 (링커 없음)
- ASM을 `.include "driver.s"`로 소스 레벨 결합
- 하드웨어 루틴 주소 고정 (`0x1000` 등)

### 3.4 컴파일러 구현 타당성 (하드웨어 강화 시)

C 컴파일러·선점형 OS를 위해 논의된 ISA 확장:

- 레지스터 8 → 16 (스필 감소)
- 베이스-오프셋 주소 (`LOAD R1, [SP+4]`)
- 하드웨어 `PUSH`/`POP`
- 인터럽트·PIT (선점형 스케줄러)

→ Phase 4에서 LLVM 백엔드 또는 재귀 하향 파서로 최적화 코드 생성 가능 (단, 하드웨어 복잡도·클록 하향 트레이드오프).

---

## 4. PL-DOS 언어 전략

### 4.1 3계층 조합 (권장)

| 단계 | 역할 | 언어 |
|------|------|------|
| Boot/Driver | 하드웨어 초기화, Mailbox | **Plover Assembly** |
| OS Core | mm, sched, io | **Subset C** |
| Shell/Userland | 파일 관리, REPL | **Forth** |

### 4.2 PL-DOS 4단계 파이프라인

| Stage | 목표 | 언어/도구 |
|-------|------|-----------|
| 1 | 입출력·디버그 | Monitor / **Forth (ROM)** |
| 2 | 바이너리 로드 | 호스트 크로스 컴파일 + vFDD |
| 3 | 커널 | **Subset C** (`kernel.bin`) |
| 4 | DOS 완성 | **PL-DOS** (C 커널 + Forth 쉘) |

### 4.3 Forth + C + DOS

- **DOS 쉘 ≈ Forth 인터프리터:** `FILE_LOAD`, `EXEC` 단어로 파일 시스템 노출
- C 커널이 자원 제공 → Forth가 사용자 명령 해석
- Jump Table 고정 주소 (`$0200`)로 Forth→커널 syscall

---

## 5. 개발 순서·환경

### 권장 순서

```
[하드웨어 완성] → [어셈블러] → [Forth = 최초 OS] → [Subset C 컴파일러] → [C 커널] → [PL-DOS]
```

- OS **전에** 컴파일러: 커널을 효율적으로 작성하기 위함
- Forth 완성 + 간단 커널 구동 후 → 3.3V PCB (512KB RAM, 16MHz) 전환 검토

### VM vs 하드웨어

- OS/컴파일러 논리: **`plover_vm`에서 먼저** (S0–S7 게이트)
- 브레드보드: 부트로더·하드웨어 루틴 확정
- 3.3V PCB: 실물 self-hosting·신호 무결성 (선택)

---

## 6. 결론 표

| 질문 | 답 |
|------|-----|
| Forth·Subset C 외에 뭐가 있나? | **Assembly**, **기계어**, **Python(호스트)**, **BASIC(교육/참고)**, **vCPU 바이트코드**, 역사적 **Pascal/PL/M/FORTRAN** 등 |
| Lua는? | 8비트 타겟에 **부적합** — 기각 |
| C 전체를 구현해야 하나? | 아니오 — **Subset C**로 커널·컴파일러 교육 목표 달성 |
| 여러 언어 빌드 도구? | `asdf`급 불필요 — **plover_asm + plover_cc + (소형) plover_ld + ABI** |
| 최종 사용자-facing 언어? | **Forth 쉘** (PL-DOS), 커널은 **Subset C** |

---

## 7. 원문 위치 (빠른 참조)

| 주제 | 출처 파일 | 대략적 위치 |
|------|-----------|-------------|
| SSA 컴파일러·VM·Threaded Code | 과거로-간-현대-엔지니어의-한계.md | §2, §메모리 VM, vCPU |
| 5단계 HW/SW 커리큘럼 | 과거로-간-현대-엔지니어의-한계.md | ~2009행 |
| C 필수성·Forth·BASIC·Lua | 과거로-간-현대-엔지니어의-한계.md | ~2098–2153행 |
| Forth vs C, OS 순서 | 8비트-컴퓨터-설계-고려사항.md | ~3056–3150행 |
| S5/S6 Subset C 스펙 | 8비트-컴퓨터-설계-고려사항.md | ~3157–3250행 |
| 벤치마크 시스템 언어 | 8비트-컴퓨터-설계-고려사항.md | ~3270–3398행 |
| PL-DOS 언어 조합 | 8비트-컴퓨터-설계-고려사항.md | ~3497–3647, ~3658행 |
| Forth 철학·Lua vs Subset C | 8비트-컴퓨터-설계-고려사항.md | ~3915–4034행 |
| Stage 1–4 언어 로드맵 | 8비트-컴퓨터-설계-고려사항.md | ~5195–5228행 |
