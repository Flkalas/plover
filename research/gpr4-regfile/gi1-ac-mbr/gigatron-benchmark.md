# Gi1 — Gigatron / Isetta / rev G benchmark

**Parent:** [README.md](README.md)  
**Non-normative** comparison for design rationale only.

---

## Summary table

| | **Gigatron** | **Isetta** | **rev G** | **Gi1** |
|---|-------------|------------|-----------|---------|
| **Clock** | 6.25 MHz | 12.5 MHz | 2 MHz | **2 MHz** |
| **Inst/cycle** | ~1 native | ~1 micro | 3-phase macro | 3-phase (2-phase option) |
| **AC / main reg** | AC (377) | A | R0 | **R0** |
| **Operand B** | bus / AC path | T reg / RAM | **R1 GPR** | **MBR 574** |
| **ALU result** | AC | A / dst | **R2** | **R0** |
| **Reg-reg move** | rare / bus | microcode | **TFR** | **none** |
| **Extra vars** | RAM | **RAM (X,Y,S)** | R0–R2 + TFR | **RAM** |
| **Selectable RF** | no | microcoded | fixed R0/R1 | **fixed R0** |
| **Plover pins** | N/A | N/A | 31/32 DP | **~18/32** |
| **ADD ph2 @ 2M** | N/A | N/A | PASS | **PASS (more slack)** |

---

## What Gi1 borrows

| From | Borrowed | Not borrowed |
|------|----------|--------------|
| **Gigatron** | AC-centric ALU; mem for extra state | 1 inst/clk; 6.25 MHz; native 17-op ISA |
| **Isetta** | RAM as “extra registers” | 12.5 MHz; dual R/W bus; Z80/6502 ISA |
| **rev G** | 2 MHz; MBR fetch; idx5 FSM; ALU8 breadboard | R1/R2 GPR; TFR; ADD→R2 |

---

## What Gi1 avoids (vs P1 / P1M1)

| P1 problem | Gi1 |
|------------|-----|
| `q_bus` TDM | **no TDM** |
| 4-GPR `r_sel` | **no r_sel** |
| 500 ns ph2 / dual 574 | **250 ns ph2** |
| +574 BOM | **BOM unchanged** |

---

## Trade-off

Gi1 is the **lowest-risk timing path** on 2×1504 + rev G BOM at the cost of **ISA semantics** (no TFR, ADD clobbers AC path semantics) and **no 4-GPR**.

**Recommended when:** timing closure at **2 MHz** matters more than register-file flexibility.

---

## References (external)

- [Gigatron specs](https://gigatron.io/posts/482.html)
- [Isetta TTL computer](https://hackaday.io/project/190345-isetta-ttl-computer)
