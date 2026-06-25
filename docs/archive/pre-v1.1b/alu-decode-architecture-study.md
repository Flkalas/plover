# ALU decode architecture study

**Tools:** [`tools/alu_decode_search.py`](../../tools/alu_decode_search.py) · [`tools/alu_decode_arch.py`](../../tools/alu_decode_arch.py)  
**Related:** [`alu-opcodes-timing.md`](alu-opcodes-timing.md) §2

Opcode 재배치와 decode 구현 방식(SOP / lgc_direct / 74HC154 / CW 직결 / CPLD)을 **DIP · 고급 블록 · 게이트** 3축으로 비교합니다.

---

## 1. 아키텍처 요약

```text
                    ┌─────────────────────────────────────────┐
  ALU_OP[3:0] ─────►│ sop / lgc_direct: 04+08+32 SOP          │──► cin, b_sel, b_const_sel
  (from 574 CW)     │ hc154: 74HC154 + 74HC00 NAND glue       │──► cmp_n
                    │ cw_direct: (no block — CW bits direct)   │
                    │ cpld: absorbed in ATF1504 (MC budget)    │
                    └─────────────────────────────────────────┘
  lgc_direct only:  ALU_OP ──wire──► lgc3:0 (logic ops); y_mux = OR(lgc*) local
```

| Arch | 추가 DIP (lgc_direct 기준) | advanced | 게이트 | 비고 |
|------|---------------------------|----------|--------|------|
| `sop` | 9 | 0 | 37 | 자동 넷리스트; BOM 08/32/04 재사용 |
| `lgc_direct` | 10 | 0 | 40 | SOP + y_mux OR 3게이트 |
| `hc154` | 3 (decode 2 + local 32×1) | 1 | 7 | 154+00; NAND glue |
| `cw_direct` | **0** | 0 | 0 | `pack_control_store` / CW breaking |
| `cpld` | 0 | 1* | 0 | *feasible if MC ≤ budget (default 5) |

---

## 2. lgc_direct 최적 산술 opcode (SOP 37 gates)

| 그룹 | Op | `ALU_OP` |
|------|-----|----------|
| zero | NOP, ADD | `0x0` |
| sub | SUB | `0xB` |
| inc | INC | `0xD` |
| dec | DEC | `0xE` |
| cmp | CMP | `0xF` |

논리 opcode 고정: AND/PASS=`0x1`, XOR=`0x6`, OR=`0x7`, NOT=`0x8`.

**74HC154 glue (default layout):** cin ← NAND(Y11,Y15); b_sel ← 2×NAND tree on {11,14,15}; b_const ← NAND(Y13,Y14); cmp_n ← Y15 직결 → **4 NAND → 1×74HC00**.

SOP 게이트 최적과 154 NAND 수는 동일 permutation에서 같게 나오는 경우가 많으나, **다른 목표(154 dips vs SOP gates)면 opcode 배치가 달라질 수 있음** — `--pareto`로 확인.

---

## 3. CLI

```bash
# SOP 게이트만 (기본)
python tools/alu_decode_search.py --profile lgc_direct

# 다목적 Pareto (DIP / advanced / gates)
python tools/alu_decode_search.py --pareto --profile lgc_direct --top 10

# 아키텍처 subset + JSON
python tools/alu_decode_search.py --pareto --arch sop,hc154,cw_direct --json build/decode_pareto.json

# 병렬 (기본: 모든 CPU 코어; ALU_DECODE_JOBS 환경변수로 override)
python tools/alu_decode_search.py --pareto --profile lgc_direct --jobs 32
```

`lgc_direct` 산술 배치는 **95,040** permutation 완전 탐색. `--jobs N`으로 `ProcessPoolExecutor` 병렬화 (Windows: `if __name__ == "__main__"` 필수).

---

## 4. Pareto 코너 (가설)

- **cw_direct:** DIP 0 — microcode가 `cin`/`b_sel`/… 를 직접 기록 (Flash 이미 있음).
- **hc154:** ALU_OP DIP 테스트 유지 + decode **~2 DIP** (154+00).
- **sop:** 추가 주문 없음, **~9 DIP**.

`cw_direct`는 동일 assignment에서 `(dips,adv,gates)=(0,0,0)`으로 다른 arch를 dominate — 하드웨어 구현 후보 비교 시 `--arch sop,hc154`로 CW를 제외하는 것이 유용합니다.

---

## 5. 채택 체크리스트

- [ ] `tools/alu8_cases.py` opcode index
- [ ] `tools/pack_control_store.py` → `cw.hex`
- [ ] `docs/hw-bringup/b3-opcode.md` regenerate
- [ ] `gen_alu_decode_netlist.py` 또는 154 glue 넷리스트
- [ ] BOM: 74HC154 / 74HC00 주문 (hc154 선택 시)

---

## 6. 후속 (범위外)

- hwsim `74HC154` 타이밍 모델
- `gen_alu_decode_netlist.py` 154 YAML 생성
- CW 직결 시 [`microcode-spec.md`](microcode-spec.md) B7–B4 재정의
