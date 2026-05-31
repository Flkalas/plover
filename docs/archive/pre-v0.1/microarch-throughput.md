# Von Neumann 처리량 최적화 — 마이크로아키텍처 기법

**버전:** 0.3 · **기준일:** 2026-05-31  
**확정 2-기법 조합 (단일 SRAM):** **Phase Collapsing + Shadow ACC** → v1.0 stretch ~1.33 MIPS  
**v1.1 ACC:** Collapsing 유지 — **~0.5–1.0 MIPS** realistic ([arch-bom-tradeoffs-v1.1.md](arch-bom-tradeoffs-v1.1.md))
**전제:** 12종 ALU opcode ([`alu8.md`](../hw/netlist/blocks/alu8.md)) · **2.0 MHz** 시스템 클록 · 공유 SRAM 폰 노이만 · 16비트 ISA (opcode + operand)

현재 저장소는 **ALU 블록만** hwsim으로 검증 중입니다. 본 문서는 CPU 통합 재개 시 적용 후보 기법과 **타이밍·IPC 검토**를 기록합니다.

---

## 1. 목표

| 항목 | 값 |
|------|-----|
| 클록 | 2.0 MHz (500 ns 주기, **250 ns** 반주기) |
| ALU | 12 opcode 고정 ([`hw-bringup-b3-opcode.md`](hw-bringup-b3-opcode.md)) |
| 구조 | 다중 사이클 Von Neumann (Fetch → Decode → Execute…) |
| 성능 목표 | **1.0 MIPS** floor · **~1.33 MIPS** stretch (Collapsing + Shadow ACC) |
| 참조 | MOS 6502 φ₁/φ₂ 인터리브, Apple II 메모리 시분할 |

하버드/VLIW(v0.2)의 CPI ≈ 1 대비, 공유 버스·다중 사이클 FSM은 CPI 팽창이 불가피합니다. 아래 기법은 **IPC(Instructions Per Cycle) 회복**을 위한 설계 옵션입니다.

---

## 2. 하드웨어 데이터 패스·제어망 기법

| 기법 | 메커니즘 | IPC / CPI 파급 (추산) |
|------|----------|------------------------|
| **클록 위상 분할 메모리 인터리빙** | 클록 **HIGH**에서 명령 인출(Fetch, PC→SRAM/Flash 주소, IR 래치), **LOW**에서 데이터 읽기/쓰기(Execute, `{R1,R0}` 등 유효 주소). SRAM `CE`/`OE`/`WE`를 FSM 위상과 묶어 **물리 버스 충돌 회피**. | 공유 단일 SRAM에서도 fetch와 data access **시간 분할**. 순차 코드에서 CPI **1.5 ~ 2.0** 구간 목표 (6502와 동일 계열). |
| **물리 16비트 SRAM 뱅크** | `IS62C256` **2기**: Even/Odd 뱅크 병렬, `A[15:1]` 공유·`A0`로 뱅크 선택. Fetch 위상에서 **16비트 워드**(opcode ∥ operand) 단일 주기 수신. | Fetch **2바이트 → 1메모리 사이클**로 압축. 16비트 ISA fetch 병목 **원천 제거** — CPI 하한에 가장 직접적인 물리적 해법. |
| **비동기 명령 프리페치** | Execute 하반부에 **PC+1** 주소 선행, 다음 명령 프리페치 래치. | 순차 IPC ↑ — **단, 단일 `IS62C256` + 245 중재 없이는 물리 불가** (§5.4). |

---

## 3. 마이크로 시퀀서(FSM) 펌웨어·논리 튜닝

| 기법 | FSM 변경 | MIPS 마진 |
|------|----------|-----------|
| **디코딩 위상 병합 (Phase Collapsing)** | T1 **하강 에지** IR 래치 직후 **독립 T2(Decode) 클록 제거**. `{IR[15:8], phase=0}` → Flash 제어 워드(CW) comb 방출 → 다음 Execute macro-cycle 준비. | Baseline **3 macro-CPI → 2 macro-CPI**. 2.0 MHz × (1/2) = **1.0 MIPS** 방어선. |
| **하드와이어드 섀도우 ACC** | ALU `Y` ↔ B 입력 사이 **`74HC574` 순환 경로** — 1 macro-cycle 중간 결과 캐시. 외부 SRAM/MUX 왕복 감소. | ACC·카운터·내적형 루프에서 **메모리 CPI 제거**. B3c의 [`574 ACC`](../hw/netlist/blocks/alu_b3_clock.yaml)를 CPU 데이터패스로 확장. |

---

## 3.5 확정 조합 — Phase Collapsing + Shadow ACC (단일 SRAM)

단일 공유 SRAM(`IS62C256`) 물리 계층에서 **Prefetch는 Execute 위상의 LOAD/STORE와 주소·데이터 버스가 필연적으로 중첩**합니다. `74HC245` 및 AddrMUX 제어 없이 Prefetch를 단독 적용하는 것은 **버스 경합(Bus Contention)** 으로 물리적으로 불가합니다.

| 적용 기법 | 런타임 제어 | 성능 파급 | 물리 리스크 |
|-----------|-------------|-----------|-------------|
| **Phase Collapsing** | T2(Decode) macro-cycle **소거**. T1 fetch 하강 에지 IR latch → Flash `{opcode,phase=0}` comb → T3(Execute) 직행. | 3 → **2 macro-CPI** → **1.0 MIPS** floor | Flash **70 ns**가 IR/574 setup 마진 침식 가능 |
| **Shadow ACC** | ALU `Y` → `74HC574` → B-side `153` MUX (`b_src_sel`). SRAM 왕복 없이 중간값 순환. | ACC·카운터 루프에서 **평균 CPI → ~1.5** → **~1.33 MIPS** | B3c 검증 재사용; ALU 출력 bus **C_load** 국소 증가 |

**수식:** `MIPS = f_clk / CPI_avg` → 2.0 MHz / 1.5 ≈ **1.33 MIPS**. Collapsing만으로 1.0, ACC bypass로 메모리 op 비율이 줄어든 **코드 mix**에서 stretch 달성.

### 제어·데이터패스 스켈레톤 (hwsim netlist 목표)

개념 YAML — CPU 재구현 시 `cycle_fsm` / datapath generator 입력:

```yaml
# cycle_fsm — Phase Collapsing (T2 생략)
states:
  T1_FETCH:
    out: { ir_we: 1, pc_inc: 0, sram_oe: 1 }
    next: T3_EXECUTE          # T2_DECODE 완전 소거
  T3_EXECUTE:
    out: { ir_we: 0, pc_inc: 1, sram_oe: _opcode_dep }
    next: T1_FETCH

# alu_datapath — Shadow ACC (B3c 확장)
components:
  - { type: 74HC574, id: shadow_acc, in: { d: alu_out, cp: acc_we } }
  - { type: 74HC153, id: alu_b_mux, in: { i0: sram_data, i1: shadow_acc_q, s: b_src_sel } }
```

**주의:** 실제 v1.0 설계는 **프로그램 SRAM fetch** + **Flash 제어 ROM `{IR[15:8], phase}`** 이원 구조입니다. 위 `sram_oe`는 fetch 위상; Execute 시 CW는 Flash comb. 통합 netlist에서는 두 메모리 포트를 AddrMUX로 분리해야 합니다.

### hwsim 선제 검증 (CPU 재개 gate)

| 테스트 | 검증 항목 |
|--------|-----------|
| `fdmerge_timing` | T1 ↓ IR latch → Flash 70 ns → CW stable → T3 entry (T2 없음) |
| `collapse_fsm` | FSM T1→T3 only; `pc_inc` 타이밍 vs branch |
| `shadow_acc_rmw` | `b_src_sel=ACC` 연속 ADD chain; 574 setup @ 250 ns |
| `setup_hold` | IR, shadow_acc CP, regfile CP — falling/posedge 모두 |

T1→T3 직행 구간에서 **IR 안정화 + Flash + ALU comb**가 250 ns half-window를 넘지 않는지 slack ≥ 0 확인 전 **브레드보드 FSM 록업 금지**.

---

## 4. 타이밍 예산 (2.0 MHz)

### 4.1 반주기 250 ns 내 주요 지연

| 구간 | typ (hwsim / datasheet) | 출처 |
|------|-------------------------|------|
| SRAM 주소→데이터 | 45 ns | [`IS62C256`](../hw/timing/memory.yaml) |
| Flash 제어 ROM | 70 ns | [`SST39SF010A`](../hw/timing/memory.yaml) |
| 574 setup (ACC) | ≤ 15 ns (max 모드) | `bringup_b3c_clock` slack 경로 |
| regfile+ALU comb (Flash 제외) | **~228 ns** E2E, slack ~22 ns | [BOM.md](../BOM.md) regfile slack study |

### 4.2 위상 분할 시 한 macro-cycle 타임라인 (개념)

```text
         ┌──────── 500 ns macro-cycle ────────┐
clk2  ───┤ HIGH (φ_fetch) │ LOW (φ_exec/mem) ├───
         │ PC→addr, IR←   │ AddrMUX, R/W, ALU│
         └─────────────────┴──────────────────┘
              ~250 ns            ~250 ns
```

- **φ_fetch:** PC 안정 → SRAM/Flash read → (posedge 또는 **falling edge**) IR latch.
- **φ_exec:** 유효 주소 → SRAM read/write; 또는 Flash `{opcode,phase}` → CW → regfile/ALU.

### 4.3 Phase Collapsing — 교정된 2-macro-cycle 타임라인

T2(500 ns) macro-cycle을 **논리적으로만** 제거합니다. Flash+datapath를 T1 **LOW 125 ns**에 넣지 **않고**, **T1↓ → T3↑** 사이 **250 ns** 창을 Execute comb 예산으로 씁니다.

```text
  0 ns          250 ns         500 ns         750 ns
  │   T1 (Fetch)   │   (prep)   │  T3 (Exec)  │
clk ─┐           ┌─┴──────────┐           ┌─┴──
     └───────────┘            └───────────┘
     ↑ PC→SRAM      ↓ IR latch    ↑ reg CP (목표)
                    Flash addr ON
                    │←─ 250 ns ─→│
                    70 Flash + ~158 comb (목표)
```

| 위상 | 클록 에지 | 동작 | 예산 |
|------|-----------|------|------|
| **T1 Fetch** | ↑ Rising | PC → AddrMUX → SRAM; `sram_oe`=1 | 250 ns (SRAM `t_aa` 45 ns 여유) |
| **T1 Latch** | ↓ Falling | SRAM → IR latch; Flash `{IR[15:8],phase}` 주소 전환 | 전이점 |
| **T3 Execute** | ↑ Rising (다음 macro-cycle) | CW stable → regfile decode → ALU → **reg setup** | T1↓ 이후 **250 ns** |

**⚠ 228 ns 함정:** v0.2 **228 ns E2E는 Flash 70 ns 미포함** (regfile→ALU만). 순차 합 **70+228=298 ns > 250 ns** 이면 T3↑ posedge 래치는 **2 MHz에서 성립하지 않을 수 있음**. hwsim gate:

| 대안 | 설명 |
|------|------|
| **A. T3↓ 래치** | Execute reg CP를 T3 **falling** — comb 예산 500 ns (T1↓→T3↓) |
| **B. CW 중간 래치** | T1↓+70 ns에 CW 574/153 hold; T3↑에는 regfile+ALU만 (~158 ns) |
| **C. 클럭 완화** | 통합 경로 slack FAIL 시 ~1.7 MHz |

Collapsing의 확정 이득은 **T2 macro-cycle(500 ns) 제거**이며, T1↓→T3↑ 250 ns 내 **전 경로** slack ≥ 0은 **별도 hwsim 증명** 필요.

### 4.4 메모리 버스 이원화 (SRAM + Flash)

| 컴포넌트 | 버스 | 제어 | 역할 |
|----------|------|------|------|
| **IS62C256** | AddrMUX(`157`) + 8b 데이터 버스 | FSM `sram_oe`/`sram_we` | Von Neumann: **프로그램 + 데이터** |
| **SST39SF010A×2** | IR[15:8]+phase → Flash 전용; **메인 데이터 버스 미연결** | Flash `OE`/`CE`, CW comb | **마이크로 CW** decode |

Fetch는 SRAM, Execute 제어는 Flash — AddrMUX가 **PC vs effective address** (SRAM)만 arbitration; Flash 주소는 IR 병렬 파생.

### 4.5 분기 FSM (검증 스켈레톤)

```yaml
# cycle_fsm_branch_sync.yaml — 개념; phase_rst active-high 가정
states:
  T1_FETCH:
    out: { ir_we: 1, pc_inc: 0, sram_oe: 1, phase_rst: 0 }
    next: T3_EXECUTE
  T3_EXECUTE_NORMAL:
    out: { ir_we: 0, pc_inc: 1, sram_oe: _opcode_dep, phase_rst: 0 }
    next: T1_FETCH
  T3_EXECUTE_BRANCH_TAKEN:
    out: { ir_we: 0, pc_load: 1, pc_inc: 0, phase_rst: 1, sram_oe: 0 }
    next: T1_FETCH   # 다음 T1↑: PC→SRAM setup_hold (45 ns) 검증 필수
```

`T3_EXECUTE_NORMAL`의 `phase_rst: 1`은 **오류** — increment만; reset은 **branch taken** 전용. Branch 시 PC load + phase_rst 동시 → 157/MUX **SSO** → decoupling·DSO lock-up margin.

---

## 5. 검토 (feasibility)

### 5.1 종합 평가

| 기법 | 타당성 | IPC 기대 | 브레드보드 난이도 | hwsim 선행 |
|------|--------|----------|-------------------|------------|
| 위상 분할 인터리빙 | **높음** — 6502 검증 패턴 | CPI 1.5~2.0 (코드 mix 의존) | 중 — 2상 `CE`/`OE` 배선 | cycle_fsm + addr_mux |
| 16비트 SRAM 뱅크 | **높음** — fetch 대역 최적 | Fetch CPI −1 | 중 — 칩 +2, A0 디코드 | dual-port behavioral SRAM |
| 프리페치 래치 | **단일 SRAM: 불가** (§5.4) | — | 245+MUX 필수 | — |
| Phase Collapsing | **중~높음** — Flash 70 ns 여유 | 3→2 macro-CPI | 중 — FSM variant | `v1_fdmerge_timing` 유형 재도입 |
| Shadow ACC | **높음** — B3c와 동일 574 | 루프 한정 ↑ | **낮음** — B3c 검증됨 | `alu_b3_clock` 재사용 |

### 5.2 사용자 분석에 대한 기술적 코멘트

**클록 하강 에지 의존성**  
다중 사이클 FSM에서 IR latch·phase reset을 **falling edge**에 두면, 브레드보드의 **기생 C + 74HC 입력 임계**로 duty skew·jitter가 setup/hold를 직접 깎습니다. 문서화된 선결 과제로 적절합니다.

- **권장:** `74HC14` (Schmitt) 클록 버퍼/tree, φ_fetch/φ_exec **비중첩** 구간(dead time) 확보 — [`Gemini-_28` archive](archive/gemini/Gemini-_28.md)의 2상 non-overlap 논의와 일치.
- **검증 순서:** hwsim `setup_hold` → DSO 실측 (duty, rise/fall, CH-CH skew) → FSM silicon.

**CPI 1.5~2.0 vs 1.0 MIPS**  
- 1.0 MIPS = 2.0 MHz / **2.0 CPI** — Phase Collapsing **2 macro-CPI**와 정확히 정합.
- CPI 1.5는 **평균**치(프리페치·ACC·즉값 op mix)로 해석해야 하며, **LOAD/STORE/분기** micro-sequence는 여전히 3+ macro-cycle 가능.

**16비트 SRAM vs Phase Collapsing**  
- 뱅크 확장: **fetch 바이트 수** 감소.
- Phase Collapsing: **macro-cycle 수** 감소.
- **직교(orthogonal)** — 둘 다 채택 시 상승 효과. Fetch가 1-cycle이면 Collapsing 이득이 상대적으로 더 큼.

**프리페치 + 단일 SRAM (§5.4)**  
Prefetch는 Execute 위상의 **동일 SRAM** R/W와 주소 버스·데이터 버스를 **동시에** 요구합니다. φ 인터리빙만으로는 “다음 PC fetch”와 “현재 effective-address access”를 같은 250 ns LOW 창에 넣을 수 없습니다. **245 + AddrMUX + `prefetch_en` 제어** 없이 1.33 MIPS를 Prefetch로 노리는 접근은 **물리적으로 배제** — Collapsing + Shadow ACC가 단일 SRAM에서의 **2-기법 최적해**.

**Shadow ACC**  
B3의 `U_REG_574_ACC`가 이미 **Y→Q** 래치를 검증했습니다. CPU 통합 시 **B mux vs ACC feed-forward** 경로를 `alu_sel`/CW로 선택하면 “섀도우 ACC”는 **신규 ALU가 아니라 regfile/MUX 확장**으로 구현 가능합니다.

### 5.3 리스크

| 리스크 | 완화 |
|--------|------|
| LOW 위상 250 ns 내 Flash+datapath 초과 | Execute 결과 **posedge 래치**; Collapsing은 T2 **클록**만 제거 |
| Falling-edge IR latch + jitter | 74HC14, 짧은 배선, DSO 캘리브레이션 |
| 분기 flush + phase reset | Branch micro-op **마지막 phase**; `Z_prev` compare 1 cycle 선행 |
| 프리페치 (단일 SRAM) | **채택 안 함** — 버스 경합 | — |

### 5.4 Prefetch 배제 근거 (단일 IS62C256)

```text
  Execute macro-cycle (T3):
    AddrMUX ← effective address  (LOAD/STORE)
    SRAM OE/WE active            ← data phase

  Prefetch (proposed overlap):
    AddrMUX ← PC+1               ← instruction fetch
    SRAM OE active               ← IR prefetch

  → 동일 A[14:0], D[7:0] 버스 — 단일 드라이버/단일 CE 없이 불가
  → 해결: 74HC245 isolate + 2-port mem OR dual SRAM bank OR Prefetch 포기
```

---

## 6. 권장 채택 (CPU 재개 — 단일 SRAM)

**확정 2-기법:** Phase Collapsing + Shadow ACC (Prefetch **미채택**).

1. **Shadow ACC** — `alu_b3_clock` → CPU datapath merge (`153` B mux).
2. **Phase Collapsing FSM** — T1→T3, hwsim `fdmerge_timing` + `setup_hold` gate.
3. *(선택)* φ_fetch/φ_exec — Collapsing 안정 후 `CE`/`OE` 위상 분할.
4. *(선택)* Dual SRAM — fetch 대역; Prefetch 대체 가능 경로.
5. ~~Prefetch~~ — **245 없는 단일 SRAM에서 제외.**

**선결 캘리브레이션 (실기 전):**

- [ ] hwsim: `setup_hold` on IR, PC→MUX→SRAM, CW→574 CP
- [ ] DSO: `net_clk2` duty, fall time, board-full skew
- [ ] 74HC14 클록 버퍼 프로토타입

---

## 7. Code Mix — 실효 MIPS 변동

**CPI 정의 (본 문서):** `CPI = (총 clk macro-cycle) / (완료된 ISA 명령 수)`. Collapsing 후 **하한 2 macro-cycle/명령** (T1+T3). Shadow ACC는 **macro-cycle을 2 미만으로 줄이지 않음** — 다중 micro-phase·메모리 op **생략**으로 **평균 CPI**를 낮춤.

| 명령어 프로파일 | 평균 CPI (추산) | MIPS @ 2 MHz | 평가 |
|-----------------|-----------------|--------------|------|
| 순차 산술 + Shadow ACC hit | **~1.5** | **~1.33** | Stretch — ACC 루프에서 LOAD/STORE micro-phase 감소 |
| 일반 LOAD/STORE 혼재 | **~2.0** | **~1.0** | Collapsing **floor** |
| 고빈도 분기 + 다중 micro-step | **2.5 ~ 3.0** | **~0.67 ~ 0.8** | phase penalty · PC load · (Prefetch flush 없음) |

**실제 소프트웨어:** 분기·메모리 op 비율이 높으면 **~1.0 MIPS로 수렴** — 1.33 MIPS는 **ACC-heavy 순차 코드**의 이론 상한에 가깝습니다.

| 구성 | macro-CPI (typ) | MIPS @ 2 MHz |
|------|---------------------------|--------------|
| Baseline Von Neumann (T1+T2+T3) | 3 | **0.67** |
| + Phase Collapsing | 2 | **1.00** |
| **Collapsing + Shadow ACC** (확정) | **~1.5 avg** | **~1.33** |
| + Dual SRAM (선택) | ~1.5 | ~1.33 (fetch op mix ↓) |
| Prefetch + 단일 SRAM | — | **물리 불가** |

*1.33 MIPS는 CPI_avg≈1.5 **코드 mix 가정**; LOAD/STORE·분기 비율↑ 시 하향.*

---

## 8. 관련 문서

| 문서 | 관계 |
|------|------|
| [roadmap-next.md](roadmap-next.md) | ALU → CPU 재개 로드맵 |
| [hw-bringup-b3.md](hw-bringup-b3.md) | Shadow ACC / 2 MHz ACC 실기 |
| [hw-sim.md](hw-sim.md) | 타이밍 검증 방법 |
| [BOM.md](../BOM.md) | IS62C256 ×2, 74HC14 추가 시 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-31 | v0.3 — Code mix 표, T1↓→T3↑ 타이밍 교정, 228+70 ns 주의, branch FSM |
| 2026-05-31 | v0.2 — Prefetch 단일 SRAM 배제; Collapsing+Shadow ACC 확정; hwsim gate |
| 2026-05-31 | v0.1 — 5종 최적화 기법, 타이밍 예산, feasibility 검토 |
