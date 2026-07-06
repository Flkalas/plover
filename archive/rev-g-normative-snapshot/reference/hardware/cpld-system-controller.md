# CPLD System Controller v1.0 rev G

**Devices:** 2× **ATF1504AS-10JU44** (PLCC-44)  
**Roles:** **CPLD-CU** — idx5 FSM + direct strobes + branch · **CPLD-DP** — GPR + full `q_a`/`q_b`  
**CE tree:** 74HC138×2 + 08/32/04 (off-chip)

**Related:** [control-and-decode.md](control-and-decode.md) · [cpld-dual-routing.md](cpld-dual-routing.md) · [cpld-dual-jtag.md](cpld-dual-jtag.md) · [microcode-spec.md](microcode-spec.md)

**Bitstream:** WinCUPL **Design fits** per device (64 MC part rating). Sources: `system_ctrl_cu.pld`, `system_ctrl_dp.pld`.

---

## 1. Design rules

1. **Fixed ALU read:** `q_a` ← R0, `q_b` ← R1 always (CPLD-DP).
2. **Write target:** `w_sel` on G-IC from CPLD-CU (LUT or TFR `opc[3:2]`).
3. **Phase FSM** on CPLD-CU only; **no Flash param fetch**; Flash `$4000` **unused**.
4. **idx5 decode:** FSM key `(opcode[4:0] << 2) | phase[1:0]` — **128 slots** on CU.
5. **Strobes:** CU drives **14 nets directly** to SoC (no external CW latch).
6. **Branch:** `PC_LOAD_EN = macro_end & lut_pc_load & (!lut_pc_flg_z | FLG_Z)` on CU.
7. **TFR:** CU detects six opcodes; exports `src[1:0]=opc[1:0]`, `w_sel=opc[3:2]` on G-IC; DP mux matches monolithic v1.0 equations.
8. **Mailbox, MAP, `/CE`** — outside CPLD.

---

## 2. CPLD-CU port list

### Inputs (7)

| Signal | Source | Role |
|--------|--------|------|
| `OPC[4:0]` | IR574 | idx5 + TFR decode |
| `FLG_Z` | FLG574 | BEQ @ macro_end |
| `CLK` | 2 MHz | Phase FSM |

### Outputs — SoC (14)

| Signal | Function |
|--------|----------|
| `MEM_RD`, `MEM_WR` | Memory strobes |
| `Y_OE` | Bus drive (STA) |
| `FLG_WE` | Flag latch write |
| `PC_LOAD_EN` | Branch commit |
| `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1` | ALU controls |

`bctrl1`/`bctrl3` fan out at 153 from `bctrl0`/`bctrl2`.

### Outputs — G-IC to CPLD-DP (6)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write (LUT ∨ TFR) |
| `w_sel[1:0]` | GPR write select |
| `tfr_valid` | TFR datapath select |
| `src[1:0]` | TFR source reg (`opc[1:0]`) |

**Pin budget:** 26/32 used (6 spare).

---

## 3. CPLD-DP port list

### Inputs (15)

| Signal | Source | Role |
|--------|--------|------|
| `d_in[7:0]` | Data bus | LDA / bus write |
| G-IC (6) | CPLD-CU | Strobes above |
| `CLK` | 2 MHz | GPR FF clock |

### Outputs (16)

| Signal | Function |
|--------|----------|
| `q_a[7:0]`, `q_b[7:0]` | Async read → ALU A/B (full 8b) |

**Pin budget:** 31/32 used (1 spare).

---

## 4. G-IC bundle

| ID | Signal | DP pin (declared) |
|----|--------|-------------------|
| G01 | `reg_we` | 12 |
| G02 | `w_sel0` | 14 |
| G03 | `w_sel1` | 16 |
| G04 | `tfr_valid` | 17 |
| G05 | `src0` | 18 |
| G06 | `src1` | 19 |

**CLK:** pin 43 both chips (parallel).

Detail: [cpld-dual-routing.md](cpld-dual-routing.md)

---

## 5. TFR behavior

| Opcode | Transfer |
|--------|----------|
| `0x11` | R0 ← R1 |
| `0x12` | R0 ← R2 |
| `0x14` | R1 ← R0 |
| `0x16` | R1 ← R2 |
| `0x18` | R2 ← R0 |
| `0x19` | R2 ← R1 |

CU: `tfr_valid` OR of six 5-bit minterms; `reg_we = reg_we_lut # tfr_valid`.  
DP: per-bit mux `!src1 & !src0 & r0x # !src1 & src0 & r1x # src1 & !src0 & r2x` when `tfr_valid`.

---

## 6. JTAG / programming

Daisy chain: programmer → **CU (TDI first)** → **DP** → programmer TDO.  
TCK/TMS paralleled. See [cpld-dual-jtag.md](cpld-dual-jtag.md).

---

## 7. ADD / CMP ph1 policy

For ALU_REG templates, **ph1 always asserts REG_WE with `w_sel=R1`** — imm8 from MBR must latch to R1 before ph2 execute.

---

## 8. MC / fit gate

| Chip | Desk estimate | Gate |
|------|---------------|------|
| CPLD-CU | ~29–35 MC | WinCUPL Design fits |
| CPLD-DP | ~18–28 MC | WinCUPL Design fits |

Do not record fitter used-MC counts as normative BOM gates — **Design fits** is the bring-up gate.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | **rev G** — dual CPLD; direct strobes; G-IC 6-wire; full `q` |
| 2026-07-06 | Tier C monolithic spec archived |
