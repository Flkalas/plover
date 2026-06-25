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

| 코너 | 추가 DIP | delay | CPLD MC |
|------|----------|-------|---------|
| baseline | 0 | 141 ns | 38 |
| min DIP 순수 74HC (`counter_template`) | 9 | 144 ns | 26 |
| min DIP Flash (`flash_cw16_direct`) | 3 | 136 ns | 26 |

**Pareto:** `baseline_fsm` 단독 — 외부 제어는 추가 DIP 0을 이기지 못함.

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
| `tools/cpld_ctrl_arch.py` | 아키텍처 채점 |
| `tools/gen_cpld_ctrl_netlist.py` | gate netlist + catalog |
| `tools/build_cpld_ctrl_viewers.py` | HTML 뷰어 빌드 |
| `hw/netlist/research/cpld_ctrl_*.yaml` | 연구 netlist |

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
