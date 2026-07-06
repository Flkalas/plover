# I/O pin map — P1 bus-TDM

**Device:** ATF1504AS-10JU44 PLCC-44 · **32 user I/O** (JTAG reserved: 7, 13, 32, 38)  
**Parent:** [README.md](README.md) · Clock: [clock-topologies.md](clock-topologies.md)

Default topology: **C0** (OSC tap 4M to DP, 74HC74 → 2M to CU/574).  
**Desk gate:** WinCUPL **Design fits** supersedes this declaration list.

---

## 1. Delta vs rev G

| Signal group | rev G | P1 bus-TDM |
|--------------|-------|------------|
| ALU operands out | `q_a[8]` + `q_b[8]` = 16 | **`q_bus[8]`** = 8 |
| ALU A path | direct | **574 latch** ← `q_bus`; **`alu_a_le`** |
| ALU B path | `q_b` direct | **`q_bus` direct** (T2) |
| GPR read select | fixed R0/R1 | **`r_sel_a[2]`**, **`r_sel_b[2]`** on G-IC |
| GPR depth | R0–R2 | **R0–R3** |
| Clock @ DP | 2M (shared) | **4M root** (C0); GPR FF @ internal **2M** |

---

## 2. CPLD-DP — declared pins (C0)

### Inputs (19)

| Pin | Signal | Source |
|-----|--------|--------|
| 1 | `d_in0` | Data bus |
| 2 | `d_in1` | |
| 4 | `d_in2` | |
| 5 | `d_in3` | |
| 6 | `d_in4` | |
| 8 | `d_in5` | |
| 9 | `d_in6` | |
| 11 | `d_in7` | |
| 12 | `reg_we` | G-IC ← CPLD-CU |
| 14 | `w_sel0` | G-IC |
| 16 | `w_sel1` | G-IC |
| 17 | `tfr_valid` | G-IC |
| 18 | `src0` | G-IC |
| 19 | `src1` | G-IC |
| 20 | `r_sel_a0` | G-IC |
| 21 | `r_sel_a1` | G-IC |
| 22 | `r_sel_b0` | G-IC |
| 23 | `r_sel_b1` | G-IC |
| 43 | `clk_4m` | 4 MHz OSC (tap) |

### Outputs (9)

| Pin | Signal | Destination |
|-----|--------|-------------|
| 3 | `q_bus0` | 574 D0, ALU B0 |
| 10 | `q_bus1` | 574 D1, ALU B1 |
| 15 | `q_bus2` | 574 D2, ALU B2 |
| 24 | `q_bus3` | 574 D3, ALU B3 |
| 25 | `q_bus4` | 574 D4, ALU B4 |
| 26 | `q_bus5` | 574 D5, ALU B5 |
| 27 | `q_bus6` | 574 D6, ALU B6 |
| 28 | `q_bus7` | 574 D7, ALU B7 |
| 29 | `alu_a_le` | 574 **LE** (active-high pulse @ T1 end) |

### Pin budget

| | Count |
|---|------:|
| In | **19** |
| Out | **9** |
| **Σ** | **28** / 32 |
| **Spare** | **4** |

Spare pads (desk reserve): 33, 34, 35, 36, 37, 39, 40, 41, 42 — use for **C2** `clk_2m_out` or debug.

---

## 3. CPLD-CU — unchanged base + C1 option

### rev G base (26/32)

| Dir | Signals | Count |
|-----|---------|------:|
| In | `opc[4:0]`, `flg_z`, `clk` | 7 |
| Out SoC | strobes 14 | 14 |
| Out G-IC | `reg_we`, `w_sel`, `tfr_valid`, `src[1:0]` | 6 |
| **Σ** | | **26** |

**G-IC extension for P1:** CU LUT drives **`r_sel_a[1:0]`** and **`r_sel_b[1:0]`** on **four additional CU outputs** routed to DP pins 20–23.

| | Count |
|---|------:|
| Out G-IC extended | 6 + 4 = **10** |
| **CU Σ (P1)** | 7 + 14 + 10 = **31** / 32 |

**CU spare under P1:** **1** (unless C1 clock exports consume 1–2 more).

### C1 clock exports (optional)

| Pin (desk) | Signal |
|------------|--------|
| 33 | `clk_2m_out` |
| 34 | `clk_1m_out` |

CU @ C1: 31 + 2 = **33** — **FAIL** unless one SoC strobe moved or debug export dropped. **C1 with dual export needs pin trade** or **C2 DP export** instead.

---

## 4. G-IC bundle (CU → DP)

| ID | Signal | DP pin | Notes |
|----|--------|--------|-------|
| G01 | `reg_we` | 12 | unchanged |
| G02 | `w_sel0` | 14 | 4-way decode in DP |
| G03 | `w_sel1` | 16 | |
| G04 | `tfr_valid` | 17 | |
| G05 | `src0` | 18 | |
| G06 | `src1` | 19 | |
| G07 | `r_sel_a0` | 20 | **new** — stable 250 ns in execute |
| G08 | `r_sel_a1` | 21 | **new** |
| G09 | `r_sel_b0` | 22 | **new** |
| G10 | `r_sel_b1` | 23 | **new** |

**Inter-chip wires:** 6 → **10** (+4 vs rev G).

---

## 5. SoC wiring changes

| Net | rev G | P1 |
|-----|-------|-----|
| `net_a0..7` | CPLD `q_a` | **574 Q** (latched A) |
| `net_b0..7` | CPLD `q_b` | CPLD **`q_bus`** (live B @ T2) |
| `net_clk2` | 74HC74 Q | C0: same; C1/C2: CPLD export |
| 574 ALU-A | — | **+1 DIP** (#11 inventory → 4×574) |

### 574 ALU-A latch

| 574 pin | Connection |
|---------|------------|
| D[7:0] | `q_bus[7:0]` |
| LE | `alu_a_le` |
| CP | `net_clk2` (2 MHz) — **not** 4 MHz |
| OE# | GND (always drive A nets) |

GPR / PC / MBR / FLG 574s remain on **`net_clk2`**.

---

## 6. Topology-specific pin 43

| Topology | CPLD-DP pin 43 | CPLD-CU pin 43 |
|----------|----------------|----------------|
| **C0** | `clk_4m` (OSC) | `clk_2m` (74HC74) |
| **C1** | `clk_4m` (OSC) | `clk_4m` (OSC) |
| **C2** | `clk_4m` (OSC) | `clk_2m` (DP export) |

---

## 7. Comparison to P0

| Path | DP I/O | vs 32 |
|------|--------|-------|
| P0 naive (`q_a`+`q_b`+`r_sel`) | 35 | **FAIL +3** |
| **P1 bus-TDM** | **28** | **PASS +4 spare** |

---

## 8. WinCUPL header excerpt (DP)

See [../variants/p1_dp_bus_tdm/system_ctrl.pld](../variants/p1_dp_bus_tdm/system_ctrl.pld) for full equations.

```text
PIN 43 = clk_4m;
PIN 20..23 = r_sel_a/b;
PIN  3,10,15,24..28 = q_bus0..7;
PIN 29 = alu_a_le;
```

---

## Related

- [timing-cross-domain.md](timing-cross-domain.md)
- [../variants/p1_dp_bus_tdm/README.md](../variants/p1_dp_bus_tdm/README.md)
