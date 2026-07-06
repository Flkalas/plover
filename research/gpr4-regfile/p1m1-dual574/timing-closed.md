# P1M1 timing — closed compute half

**Parent:** [README.md](README.md)  
**Fetch half:** [../p1-bus-tdm/timing-cross-domain.md](../p1-bus-tdm/timing-cross-domain.md) §3–4, §6.1  
**Budget:** 250 ns per `clk_2m` half; **500 ns** for full ph2 execute

**Label:** Desk analysis (datasheet max + 15 ns wire). Not oscilloscope verified.

---

## 1. Two-half model

| Half | Time (ns) | `op_fetch` | Activity |
|------|-----------|------------|----------|
| **Fetch (ph2a)** | 0–250 | 1 | T1 latch A; T2 latch B |
| **Compute (ph2b)** | 250–500 | 0 | ALU comb; `REG_WE`/`FLG_WE` @ 500 |

```text
  clk_2m   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\___________________/‾
           |  fetch 250ns | compute 250ns |↑ WE
  op_fetch 1111111111111111000000000000000000
  q_bus     [A][B]         (high-Z / gated)
  net_a/b   stable after LE  stable → ALU → Y
```

---

## 2. Fetch half (0–250 ns) — recap

From P1 [timing-cross-domain.md §3](../p1-bus-tdm/timing-cross-domain.md):

| Check | Result |
|-------|--------|
| 574 A setup @ `alu_a_le` ↑ (125 ns) | **PASS** (~77 ns margin max) |
| 574 B setup @ `alu_b_le` ↑ (250 ns) | **PASS** (same class as A; `q_bus` stable ~40 ns before LE) |

**`alu_b_le`:** one-shot on **rising** `u_phase` (end of T2) @ 250 ns within fetch half — same structure as `alu_a_le` @ 125 ns.

| Event | max (ns) |
|-------|----------|
| `r_sel_b` valid @ 125 | 125 |
| `q_bus` stable | 125 + 25 + 15 = **165** |
| `alu_b_le` ↑ | **250** |
| Setup margin | 250 − 165 − 8 = **77 ns** **PASS** |

---

## 3. Compute half (250–500 ns) — closed path

Operands: **574 Q** drives ALU (not live `q_bus`).

| Event | max (ns) |
|-------|----------|
| B latched @ 250; 574B `tCO` | **275** |
| A latched @ 125; stable long before 250 | **150** |
| **t_ALU_start** | **max(150, 275) = 275** |

### Opcode slack @ 500 ns (`REG_WE` edge)

| Op | Path (ns) | Y @ (ns) | Slack |
|----|-----------|----------|-------|
| AND/OR/XOR | 46 | 321 | **+179** PASS |
| ADD | 108 | 383 | **+117** PASS |
| SUB | 136 | 411 | **+89** PASS |
| INC | 153 | 428 | **+72** PASS |
| CMP (flags) | 136 + FLG ~23 | ~434 | **+66** PASS |

**Desk verdict:** P1M1 **closes** all listed ALU paths vs P1 basic single-half FAIL.

---

## 4. Comparison

| Variant | ADD Y @ | vs 250 ns | vs 500 ns |
|---------|---------|-----------|-----------|
| P1 basic (B live) | ~273 | **FAIL** | — |
| P1M1 compute half | ~383 | — | **PASS +117** |

---

## 5. Bus contention (compute half)

| Hazard | P1M1 rule |
|--------|-----------|
| `q_bus` vs `Y_OE` | TDM **gated** when `op_fetch=0`; `q_bus` not driven for ALU |
| `MEM_RD` during ph2b | FSM: `MEM_RD=0` during compute |
| `d_in` vs 574 Q | ALU Y → bus only when `Y_OE=1` for GPR write @ end of ph2b |

---

## 6. Verification gates (scope)

| # | Probe | Pass |
|---|-------|------|
| V1 | `alu_b_le` @ 250 ns in fetch half | Pulse after `q_bus` stable |
| V2 | `net_b*` matches `r_sel_b` at T2 | Matches latched GPR |
| V3 | ADD @ 2M: R2 correct | After 500 ns ph2 |
| V4 | `op_fetch` vs `q_bus` activity | Mutually exclusive with compute |

---

## Related

- [architecture.md](architecture.md)
- [fsm-isa-delta.md](fsm-isa-delta.md)
