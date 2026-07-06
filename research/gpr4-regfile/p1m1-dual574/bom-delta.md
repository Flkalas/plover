# P1M1 BOM delta

**Parent:** [README.md](README.md)  
**Normative BOM:** [reference/project/BOM.md](../../../reference/project/BOM.md) — **not modified** by this research

---

## IC count

| IC | rev G | P1 | **P1M1** | Δ vs rev G |
|----|-------|-----|----------|------------|
| ATF1504AS-10JU44 | 2 | 2 | 2 | 0 |
| 74HC574 (operand + system) | **3** | 4 | **5** | **+2** |
| 74HC74 (÷2) | 1 | 1 (C0) | 1 | 0 |
| 4 MHz OSC | 1 | 1 | 1 | 0 |

---

## 574 allocation (P1M1)

| # | Role | rev G |
|---|------|-------|
| 1 | PC (+161) | yes |
| 2 | IR (opcode) | yes |
| 3 | MBR / operand | yes |
| 4 | FLG | yes |
| — | **ALU-A latch** | — |
| — | **ALU-B latch** | — |

**rev G:** 3×574 listed in [breadboard-wiring.md](../../../reference/hw-bringup/breadboard-wiring.md) (PC, MBR, FLG — IR may share bring-up path).

**P1M1 desk:** **5×574** total — system 3 + **ALU A** + **ALU B**.

[BOM.md](../../../reference/project/BOM.md) #11: `74HC574` qty **3** → research note **5** if P1M1 adopted.

---

## Pin / wire impact

| Resource | Δ |
|----------|---|
| CPLD-DP I/O | +1 vs P1 (`alu_b_le`) |
| G-IC wires | same as P1 (10) |
| `q_bus` fanout | 2×574 D inputs (8 wires each) |
| ALU A/B from 574 Q | 16 wires (replaces 16 from CPLD `q_a`/`q_b`) |

---

## Power / area (desk)

- +1 DIP 574: ~20 mA typ @ 5 V (budget note for bring-up)
- Breadboard: place ALU-A/B 574 adjacent to ALU block to minimize `q_bus` / `net_a`/`net_b` length

---

## Related

- [pin-map.md](pin-map.md)
- [SUMMARY-REPORT.md](SUMMARY-REPORT.md)
