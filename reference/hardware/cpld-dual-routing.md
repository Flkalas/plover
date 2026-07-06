# Dual CPLD breadboard routing (rev G)

**Pins:** [cpld-system-controller.md](cpld-system-controller.md) · **Bring-up:** [breadboard-wiring.md](../hw-bringup/breadboard-wiring.md)

---

## Topology

```text
  IR/FLG ──► CPLD-CU ── G-IC (6) ──► CPLD-DP ◄── data bus
                │                      │
                └── strobes (14) ──────┼──► ALU / MEM / PC
                                       └── q_a/q_b (16) ──► ALU
```

---

## PLCC co-placement

Place **CPLD-CU** and **CPLD-DP** on **adjacent 830-tie rows**, pin-1 aligned.

| Rule | Rationale |
|------|-----------|
| G-IC on inner tie row | Short CU→DP for `reg_we`, `tfr_valid`, `src` |
| DP `q` to ALU on outer edge | 16 wires; avoid crossing G-IC |
| IR/FLG → CU only | DP has no `opc`/`flg_z` |
| Wire length ≤ 10 cm | Inter-chip timing budget |

---

## G-IC bundle (CU → DP)

| ID | Signal | DP pin |
|----|--------|--------|
| G01 | `reg_we` | 12 |
| G02 | `w_sel0` | 14 |
| G03 | `w_sel1` | 16 |
| G04 | `tfr_valid` | 17 |
| G05 | `src0` | 18 |
| G06 | `src1` | 19 |

**CLK:** pin 43 both chips (not counted in G-IC).

---

## SoC → CU

| Signal | Width | Source |
|--------|------:|--------|
| `opc[4:0]` | 5 | IR574 |
| `flg_z` | 1 | FLG574 |
| `clk` | 1 | 2 MHz distribution |

---

## SoC ← CU strobes (14)

`mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1`.

JTAG: [cpld-dual-jtag.md](cpld-dual-jtag.md)
