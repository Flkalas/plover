# Plover v1.2 — ACC+TMP (Extended Accumulator)

**버전:** 1.2 · **기준일:** 2026-05-31  
**상태:** **권장 CPU 타겟** — v1.1 순수 ACC는 minimal fallback

스펙트럼: [arch-bom-tradeoffs-v1.1.md §7](arch-bom-tradeoffs-v1.1.md) · 구현: [v1.1-implementation-plan.md](v1.1-implementation-plan.md) (M4 v1.2 gate)

---

## 1. 개요

| | v1.1 ACC | **v1.2 ACC+TMP** | v1.0 GPR |
|--|----------|------------------|----------|
| 574 | ACC | ACC + **TMP** | R0–R3 |
| B-side MUX | 없음 | **157×4** (MEM \| TMP) | 153×8 |
| A-side | ACC | **ACC hardwired** | 153×4 |
| 추가 IC | 0 | **+5** | +12 vs v1.2 |
| MIPS (est.) | 0.3–0.5 | **0.6–0.8** | ~1.0 max |

연산 **목적지·A피연산자 = ACC 고정**. TMP는 **스왑·2변수 루프**용 scratch — GPR가 아님 (별도 주소 디코드 없음).

---

## 2. 데이터 패스

```text
                    ┌── ACC.Q ──────────────► ALU A (hardwired)
                    │
  SRAM D[7:0] ──► 157×4 ──► ALU B ──► Y ──► ACC.D (CP=acc_we)
       ▲              │
       │              └── TMP.Q
       │                    ▲
       │                    └── TMP.D ← ALU Y or swap path (µcode)
       └── MEM read (245 / sram_oe)
```

1. **A = ACC.Q** — `157`/`153` 없이 직결 → v0.2 regfile A-MUX **~114 ns** 절감에 기여.
2. **B = 157 select** — `b_sel=0` → SRAM data, `b_sel=1` → TMP.Q.
3. **결과** — 기본 ACC 래치; `MOV TMP,ACC` micro-op은 ACC→TMP **574 CP** (Y 또는 ACC.Q 버스).

---

## 3. ISA 확장 (micro-op / 매크로)

### 3.1 내부 전송 (Fetch 없음 — Execute 1 phase)

| µop / op | 동작 | MEM |
|----------|------|-----|
| `TAX` / MOV TMP,ACC | TMP ← ACC | — |
| `TXA` / MOV ACC,TMP | ACC ← TMP | — |
| `ADD TMP` | ACC ← ACC + TMP | — |
| `SUB TMP` | ACC ← ACC − TMP | — |

매크로 ISA opcode (선택):

| op | Mnemonic |
|----|----------|
| 0x10 | TAX |
| 0x11 | TXA |
| 0x12 | ADD_TMP |
| 0x13 | SUB_TMP |

### 3.2 기존 v1.1 유지

LDA/STA/CALL/RET/BEQ — [microcode-spec-v1.1.md](microcode-spec-v1.1.md).  
MEM op 시 B-src = SRAM; ALU op with TMP uses `b_sel=1`.

---

## 4. 제어 (CW 필드)

| 신호 | 역할 |
|------|------|
| `b_sel` | 0=SRAM data, 1=TMP |
| `acc_we` | ACC latch enable |
| `tmp_we` | TMP latch (from ACC or ALU Y) |
| `alu_op[3:0]` | alu8 12 opcode |

Flash CW — v0.2 포맷 재사용; `src/dst_reg` **미사용**.

---

## 5. hwsim gate (M4)

| 산출 | 테스트 |
|------|--------|
| `acc_tmp.yaml` | `alu_b3` + 157×4 B-mux + TMP 574 |
| `acc_tmp_swap` | TAX; TXA; ACC preserved |
| `acc_tmp_add` | ADD TMP chain, no SRAM between |
| `acc_tmp_timing` | slack @ 250 ns — A hardwired path |

**FAIL 시:** v1.1 pure ACC로 fallback (문서·BOM).

---

## 6. 실기

- 157×4 **ALU B 진입 직전** 배치 — alu8 `net_b0..7` stub과 결합.
- decap: 157×4 각 **0.1µF×2**, B bus **≤10 cm**.
- TMP 574 — ACC 인접 (swap setup).

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-31 | v1.2 ACC+TMP — 157 B-mux, ISA internal xfer |
