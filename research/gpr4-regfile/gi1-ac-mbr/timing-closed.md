# Gi1 timing — ph2 closed @ 250 ns

**Parent:** [README.md](README.md)  
**Budget:** 2 MHz execute half = **250 ns**  
**Reference paths:** [reference/hardware/cpld-dual-timing.md](../../../reference/hardware/cpld-dual-timing.md) · [reference/hardware/alu-opcodes-timing.md](../../../reference/hardware/alu-opcodes-timing.md)

**Label:** Desk analysis (datasheet max + wire). Not oscilloscope verified.

---

## 1. Why Gi1 closes (vs P1)

| Path | P1 @ 4 MHz | Gi1 @ 2 MHz |
|------|------------|-------------|
| Operand fetch | Sequential TDM on `q_bus` | **MBR stable at ph2 start** |
| ALU B | Live or 574 tCO delay | **MBR Q** (latched at insn fetch) |
| ALU A | 574 or mux | **R0 direct** (`q_a = r0*`, no 4:1 mux) |
| ph2 budget | 250 ns (FAIL ADD) | **250 ns PASS** |

---

## 2. ph2 timeline (max case)

Operands at ALU_REG **ph2** entry:

| Event | Time (ns) |
|-------|-----------|
| ph2 @0; `r_sel` N/A — R0 drives `q_a` | 0 |
| `q_a` valid (FF → pad tCO) | **~15–25** |
| `net_mbr` → `net_b` (held since fetch) | **0** additional |
| **t_ALU_start** | **~25** |

### Opcode slack @ 250 ns (`REG_WE` / `FLG_WE` edge)

| Op | Path (ns) | Y @ (ns) | Slack |
|----|-----------|----------|-------|
| AND/OR/XOR | 46 | 71 | **+179** PASS |
| ADD | 108 | **133** | **+117** PASS |
| SUB / CMP | 136 | **161** | **+89** PASS |
| INC | 153 | **178** | **+72** PASS |

**Desk verdict:** Gi1 **closes** all listed ALU ops within **single 250 ns ph2** — no 500 ns stretch, no TDM, no extra 574.

---

## 3. Comparison

| Variant | ADD Y @ | vs 250 ns |
|---------|---------|-----------|
| rev G (P8 path) | ~168 typ desk | PASS (+82 slack ref) |
| P1 bus-TDM | ~273 | **FAIL** |
| P1M1 (compute half) | ~383 @ 500 ns | PASS (2× half) |
| **Gi1** | **~133** | **PASS** |

Gi1 improves rev G ph2 margin by **avoiding ph1 R1 latch + second GPR read path** — B is ready at ph2 @0.

---

## 4. MBR hold hazards

| Hazard | Gi1 rule |
|--------|----------|
| ph0/ph1 reload MBR during ADD | **Forbidden** — ALU_REG template must not assert MBR LE |
| `Y_OE` vs MBR | No shared bus drive into MBR D during ph2 |
| LDA uses MBR as **address** | Different template — no ALU ph2 conflict |
| BEQ/JMP abs16 | MBR reused after macro — OK |

---

## 5. Scope verification gates

| # | Probe | Pass |
|---|-------|------|
| V1 | `net_mbr` stable through ADD ph0–ph2 | Equals fetch imm8 |
| V2 | `net_b` ≡ `net_mbr` during ph2 | Wiring |
| V3 | ADD @ 2 MHz: **R0** ← R0+imm | After ph2 |
| V4 | No `q_b` drive from CPLD | Floating / MBR only |

---

## Related

- [architecture.md](architecture.md)
- [fsm-microcode-delta.md](fsm-microcode-delta.md)
