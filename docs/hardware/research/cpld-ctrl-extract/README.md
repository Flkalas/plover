# CPLD 제어 로직 분리 연구 (cpld-ctrl-extract)

**Research only** — normative v1.0은 [cpld-system-controller.md](../../cpld-system-controller.md) FSM-in-CPLD.

## 문서

| 파일 | 내용 |
|------|------|
| [search-report.md](search-report.md) | Pareto 탐색 결과·권고 |
| [viewers/counter_template/index.html](viewers/counter_template/index.html) | `counter_template` gate/MUX 단위 뷰어 |
| [viewers/flash_cw16_direct/index.html](viewers/flash_cw16_direct/index.html) | `flash_cw16_direct` gate/MUX 단위 뷰어 |

## 도구

```bash
python tools/cpld_ctrl_search.py --pareto
python tools/build_cpld_ctrl_viewers.py
```

| 스크립트 | 역할 |
|----------|------|
| `tools/cpld_ctrl_model.py` | FSM → 제어 진리표 |
| `tools/cpld_ctrl_arch.py` | 아키텍처 비용 채점 |
| `tools/gen_cpld_ctrl_netlist.py` | 연구용 gate netlist + unit catalog |
| `tools/build_cpld_ctrl_viewers.py` | netlist → `build/` + docs viewers |

## Netlist (소스)

- `hw/netlist/research/cpld_ctrl_counter.yaml` — counter_template
- `hw/netlist/research/cpld_ctrl_cw16.yaml` — flash_cw16_direct

Unit catalog: `hw/units/research/cpld_ctrl_*.yaml`
