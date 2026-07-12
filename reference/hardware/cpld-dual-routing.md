# Dual CPLD breadboard routing (v1.0 P12)

**Pins:** [cpld-system-controller.md](cpld-system-controller.md) · **Bring-up:** [breadboard-wiring.md](../hw-bringup/breadboard-wiring.md)

---

## Topology

```text
  IR/FLG ──► CPLD-CU ── reg_we ──► CPLD-DP ◄── data bus
                │                      │
                └── strobes (14) ──────┼──► ALU / MEM / PC
                                       └── q_a (8) ──► ALU A
  MBR 574 Q ─────────────────────────────────────────► ALU B
```

---

## PLCC co-placement

Place **CPLD-CU** and **CPLD-DP** on **adjacent 830-tie rows**, pin-1 aligned.

| Rule | Rationale |
|------|-----------|
| G-IC on inner tie row | Short CU→DP for `reg_we` |
| DP `q_a` to ALU on outer edge | 8 wires |
| MBR → ALU B | Dedicated 8-wire bundle; keep ≤10 cm |
| IR/FLG → CU only | DP has no `opc`/`flg_z` |
| Wire length ≤ 10 cm | Inter-chip timing budget |

---

## G-IC bundle (CU → DP)

| ID | Signal | DP pin (desk) |
|----|--------|---------------|
| G01 | `reg_we` | 12 |

**CLK:** pin 43 both chips (not counted in G-IC).

---

## MBR → ALU B

| Net | Source | Destination |
|-----|--------|-------------|
| `net_mbr0..7` | MBR 574 Q | `net_b0..7` → ALU B |

ALU B is **not** driven from CPLD `q_b` (no `q_b` on DP).

Optional **74HC244** on MBR fanout if needed (desk: direct wire OK).

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

---

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | v1.0 P12 title; Active-only wording |
| 2026-07-07 | G-IC 1-wire; MBR→B |
