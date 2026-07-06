# Gi1 pin map — CPLD-DP / CU

**Device:** ATF1504AS-10JU44 PLCC-44  
**Parent:** [README.md](README.md)  
**Baseline:** [../baseline-rev-g.md](../baseline-rev-g.md) · [../pin-budget.md](../pin-budget.md)

---

## 1. Delta vs rev G

| Item | rev G | Gi1 |
|------|-------|-----|
| GPR in DP | R0–R2 | **R0 only** |
| ALU A | `q_a[8]` | `q_a[8]` ← R0 |
| ALU B | `q_b[8]` ← R1 | **`net_mbr` → ALU** (no CPLD `q_b`) |
| G-IC | 6 wires | **1** (`reg_we`) |
| DP I/O | 31/32 | **~18/32** |

---

## 2. CPLD-DP — declared pins (desk)

### Inputs (9)

| Pin | Signal | Notes |
|-----|--------|-------|
| 1,2,4,5,6,8,9,11 | `d_in[7:0]` | bus write → R0 |
| 12 | `reg_we` | only G-IC strobe |
| 43 | `clk` | 2 MHz |

**Removed inputs:** `w_sel[1:0]`, `tfr_valid`, `src[1:0]` (pins 14,16,17,18,19 free).

### Outputs (8)

| Pin | Signal | Destination |
|-----|--------|-------------|
| 3 | `q_a0` | ALU A0 |
| 10 | `q_a1` | ALU A1 |
| 15 | `q_a2` | ALU A2 |
| 24 | `q_a3` | ALU A3 |
| 25 | `q_a4` | ALU A4 |
| 26 | `q_a5` | ALU A5 |
| 27 | `q_a6` | ALU A6 |
| 28 | `q_a7` | ALU A7 |

**Removed outputs:** `q_b0..7` (former pins — spare).

### Budget

| | Count |
|---|------:|
| In | **9** |
| Out | **8** |
| **Σ** | **17** / 32 |
| Spare | **15** |

---

## 3. CPLD-CU — G-IC delta

| Signal | rev G | Gi1 |
|--------|-------|-----|
| `reg_we` | yes | yes |
| `w_sel[1:0]` | yes | **no** |
| `tfr_valid` | yes | **no** |
| `src[1:0]` | yes | **no** |

CU **exports 1** G-IC wire to DP (vs 6). Remaining CU pins spare for future STR / debug.

Desk CU total: **26 − 5 = ~21/32** (TFR decode logic removed internally).

---

## 4. Off-chip wiring (breadboard)

| Net | Connection |
|-----|------------|
| `net_mbr0..7` | MBR 574 Q → `net_b0..7` → ALU B |
| `q_a0..7` | CPLD-DP → ALU A (unchanged) |
| `q_b0..7` | **not from CPLD** |

Optional **74HC244** on `net_mbr` → `net_b` if fanout heavy (desk: direct wire OK).

---

## 5. Pin reuse map (rev G → Gi1 spare)

Former `q_b` pins 3,10,15,24–28 may be **unused** or reassigned in future variants (STR mux, debug).

---

## Related

- [../variants/gi1_dp/system_ctrl.pld](../variants/gi1_dp/system_ctrl.pld)
- [bom-delta.md](bom-delta.md)
