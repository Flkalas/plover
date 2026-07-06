# P1M1 pin map — CPLD-DP / CU

**Device:** ATF1504AS-10JU44 PLCC-44  
**Parent:** [README.md](README.md)  
**P1 baseline:** [../p1-bus-tdm/pin-map.md](../p1-bus-tdm/pin-map.md)

---

## 1. Delta vs P1

| Item | P1 | P1M1 |
|------|-----|------|
| `q_bus` destination | 574A D + **ALU B direct** | 574A D + **574B D only** |
| DP outputs | `alu_a_le` | `alu_a_le` + **`alu_b_le`** |
| DP I/O total | 28/32 | **29/32** |
| 574 (operand) | 1 | **2** |

---

## 2. CPLD-DP — declared pins (C0)

### Inputs (19) — unchanged from P1

| Pin | Signal |
|-----|--------|
| 1,2,4,5,6,8,9,11 | `d_in[7:0]` |
| 12,14,16,17,18,19 | G-IC: `reg_we`, `w_sel`, `tfr_valid`, `src[1:0]` |
| 20–23 | `r_sel_a[1:0]`, `r_sel_b[1:0]` |
| 43 | `clk_4m` |

### Outputs (10)

| Pin | Signal | Destination |
|-----|--------|-------------|
| 3 | `q_bus0` | 574A D0, **574B D0** |
| 10 | `q_bus1` | 574A D1, 574B D1 |
| 15 | `q_bus2` | 574A D2, 574B D2 |
| 24 | `q_bus3` | 574A D3, 574B D3 |
| 25 | `q_bus4` | 574A D4, 574B D4 |
| 26 | `q_bus5` | 574A D5, 574B D5 |
| 27 | `q_bus6` | 574A D6, 574B D6 |
| 28 | `q_bus7` | 574A D7, 574B D7 |
| 29 | `alu_a_le` | 574A LE |
| **33** | **`alu_b_le`** | **574B LE** |

### Budget

| | Count |
|---|------:|
| In | 19 |
| Out | **10** |
| **Σ** | **29** / 32 |
| Spare | **3** (34, 35, 36, …) |

---

## 3. 574 ALU operand latches

| IC | D | LE | CP | OE# | Q → |
|----|---|----|----|-----|-----|
| **ALU-A** | `q_bus` | `alu_a_le` @ T1 (125 ns) | `net_clk2` | GND | `net_a0..7` |
| **ALU-B** | `q_bus` | `alu_b_le` @ T2 (250 ns) | `net_clk2` | GND | `net_b0..7` |

---

## 4. CPLD-CU — same as P1

| | Count |
|---|------:|
| In | 7 |
| Out SoC | 14 |
| Out G-IC | **10** (`r_sel` + strobes) |
| **Σ** | **31** / 32 |

Optional future: `tdm_en` on spare CU pin to DP `op_fetch` — not in desk PLD v1.

---

## 5. Wiring delta vs rev G

| Signal | rev G | P1M1 |
|--------|-------|------|
| `net_a0..7` | CPLD `q_a` | **574A Q** |
| `net_b0..7` | CPLD `q_b` | **574B Q** |
| CPLD operand out | 16 pins | **10** (`q_bus` + 2×LE) |

---

## Related

- [../variants/p1m1_dp/system_ctrl.pld](../variants/p1m1_dp/system_ctrl.pld)
- [bom-delta.md](bom-delta.md)
