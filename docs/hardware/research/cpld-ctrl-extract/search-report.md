# CPLD 제어 로직 74HC 분리 탐색 보고서

**날짜:** 2026-06-25  
**범위:** GPR은 ATF1504 유지 · phase FSM/ALU/버스 제어만 외부 74HC(또는 Flash CW)로 분리  
**허브:** [README.md](README.md) · **뷰어:** [viewers/](viewers/)  
**도구:** `python tools/cpld_ctrl_search.py --pareto` → `build/cpld_ctrl_pareto.json` (로컬, gitignored)  
**Research (not normative):** [design-rationale-v1.0.md](../design-rationale-v1.0.md) · **Normative:** [cpld-system-controller.md](../../cpld-system-controller.md)

---

## 0. Scope

| 항목 | 내용 |
|------|------|
| **본 보고서** | CPLD 내부 FSM(~12 MC)을 빼고 74HC/Flash로 대체하는 후보 비용 |
| **고정** | GPR 3fixed(R0–R2)는 CPLD에 유지 (~26 MC) |
| **베이스라인** | v1.0 normative: `baseline_fsm` (GPR+FSM 통합, Flash CW 0행) |

> **독자 규칙:** 빵판 bring-up은 normative [cpld-system-controller.md](../../cpld-system-controller.md)만 따릅니다.

---

## 1. 분리 대상 인벤토리

**진리표:** 16 opcode × phase = **26 활성 행**. 생성: `tools/cpld_ctrl_model.py`.

---

## 2. 탐색 방법

```bash
python tools/cpld_ctrl_search.py --pareto
python tools/build_cpld_ctrl_viewers.py
```

| ID | 74HC / Flash | Flash 행 | CPLD MC | Unit viewer |
|----|--------------|----------|---------|-------------|
| `baseline_fsm` | 0 추가 | 0 | 38 | — |
| `flash_cw16_direct` | 574×2 + mux | 26 | 26 | [viewers/flash_cw16_direct/](viewers/flash_cw16_direct/index.html) |
| `counter_template` | 161+glue+153+574 | 0 | 26 | [viewers/counter_template/](viewers/counter_template/index.html) |

---

## 3. 결과 (2026-06-25)

| 코너 | 추가 DIP | delay (execute) | CPLD MC |
|------|----------|-----------------|---------|
| baseline | 0 | 141 ns | 38 |
| min DIP 순수 74HC (`counter_template`) | 9 | 144 ns | 26 |
| min DIP Flash (`flash_cw16_direct`) | 3 | 159 ns | 26 |

> **delay 열:** 이전 `136 ns`는 **ALU-only** (decode 우회 SUB)였음. E2E execute 창은 **574 Q + ALU** — §6 참고.

**Pareto:** `baseline_fsm` 단독 — 외부 제어는 추가 DIP 0을 이기지 못함.

---

## 6. Execute-phase timing (E2E)

**예산:** 2 MHz Execute 반주기 **250 ns** ([`alu-opcodes-timing.md`](../../alu-opcodes-timing.md) §5).

**도구:** `python tools/flash_cw_timing.py` · hwsim `hw/tests/cpld_ctrl_flash_exec_timing.yaml` (Flash fetch) · `cpu_cw_direct_sub.yaml` (574 이후 ALU)

### 6.1 경로 분해 (max corner, `hw/timing/*.yaml`)

| 구간 | 부품 | max (ns) |
|------|------|----------|
| CW 주소 MUX | 74HC157 | 18 |
| Flash 제어스토어 | SST39 / `ROM_CTRL` | 70 |
| 574 setup (CP↑) | 74HC574 | 8 |
| 574 Q → 제어선 | 74HC574 | 23 |
| ALU SUB (cw16 direct) | `ALU_CMP_SUB` | 136 |
| CPLD 등록 (baseline) | FSM 출력 | +5 |

### 6.2 스케줄 판정

| 스케줄 | flash_cw16_direct | 설명 |
|--------|-------------------|------|
| **Serial** (동일 반주기 MUX→Flash→574→ALU) | **FAIL** (~280 ns) | 250 ns 초과 |
| **Pipelined** (이전 반주기 CW fetch, 경계에서 574 래치, ALU만 execute) | **OK** | fetch 96 ns, execute 159 ns, slack 91 ns |

**설계 전제:** phase/opcode가 래치 edge **이전**에 CW 주소에 반영되어야 함 (counter comb 또는 lookahead). edge와 동시에만 phase가 바뀌면 pipelined도 실패.

**2× SST39 (CW 전용):** `t_ACC` 70 ns 동일 — `$4000` 오프셋은 이미지 편의만, 타이밍 이득 없음.

### 6.3 아키텍처별 E2E (@ 2 MHz, pipelined)

| 아키텍처 | ALU | fetch | execute | pipelined | serial |
|----------|-----|-------|---------|-----------|--------|
| `baseline_fsm` | 136 | 0 | 141 | OK | OK |
| `flash_cw16_direct` | 136 | 96 | 159 | OK | FAIL |
| `flash_cw10_decode` | 151 | 96 | 174 | OK | FAIL |
| `counter_template` | 136 | 0 | 144 | OK | OK |

**결론:** Flash CW는 **2 MHz에서 pipelined 스케줄로 가능**하나 serial single-half는 불가. Pareto DIP/MC 판단은 변하지 않음 — normative v1.0 FSM 유지 권고 불변.

**미모델:** 버스 글리치, D 공유 245 전환, 빵판 기생 — scope bring-up 체크리스트.

---

## 4. 권고

| 시나리오 | 권고 |
|----------|------|
| Normative v1.0 | `baseline_fsm` 유지 |
| CPLD MC 여유 | `flash_cw16_direct` |
| 교육·시퀀스 관측 | `counter_template` + unit viewer |

---

## 5. 도구·파일

| 파일 | 역할 |
|------|------|
| `tools/cpld_ctrl_model.py` | FSM → 제어 진리표 |
| `tools/cpld_ctrl_arch.py` | 아키텍처 채점 (E2E timing 필드) |
| `tools/flash_cw_timing.py` | Flash CW pipelined/serial 예산 |
| `tools/gen_cpld_ctrl_netlist.py` | gate netlist + catalog |
| `tools/build_cpld_ctrl_viewers.py` | HTML 뷰어 빌드 |
| `hw/netlist/research/cpld_ctrl_*.yaml` | 연구 netlist |
| `hw/tests/cpld_ctrl_flash_exec_timing.yaml` | Flash fetch path hwsim |

---

## 7. Unit viewers

정적 HTML (오프라인 열람, git 커밋):

| 아키텍처 | 경로 |
|----------|------|
| `counter_template` | [viewers/counter_template/index.html](viewers/counter_template/index.html) (~147 gate/MUX units) |
| `flash_cw16_direct` | [viewers/flash_cw16_direct/index.html](viewers/flash_cw16_direct/index.html) (5 units) |

재생성:

```bash
python tools/build_cpld_ctrl_viewers.py
# 또는 개별 export:
python -m hwsim export-units hw/netlist/research/cpld_ctrl_counter.yaml \
  --catalog hw/units/research/cpld_ctrl_counter.yaml \
  -o build/research/cpld-ctrl-extract/counter_template --html --embed-manifest
```

개발용 산출물: `build/research/cpld-ctrl-extract/{arch}/`

---

## Change log

| 날짜 | 변경 |
|------|------|
| 2026-06-25 | 초판 — Pareto 탐색 |
| 2026-06-25 | research/cpld-ctrl-extract 허브 + unit viewer 2종 |
| 2026-06-25 | §6 E2E Flash CW timing — pipelined OK, serial FAIL |
