# CPLD System Controller v1.0 (Gi1)

**Devices:** 2× **ATF1504AS-10JU44** (PLCC-44)  
**Roles:** **CPLD-CU** — idx5 FSM + direct strobes + branch · **CPLD-DP** — **R0 (AC) only** + `q_a`  
**CE tree:** 74HC138×2 + 08/32/04 (off-chip)

**Related:** [control-and-decode.md](control-and-decode.md) · [cpld-dual-routing.md](cpld-dual-routing.md) · [cpld-dual-jtag.md](cpld-dual-jtag.md) · [microcode-spec.md](microcode-spec.md)  
**Superseded:** rev G 3-GPR — [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md)

**Bitstream:** WinCUPL **Design fits** per device (64 MC part rating). Gi1 DP PLD spike: [archive/gpr4-regfile-research.tar.gz](../../archive/gpr4-regfile-research.tar.gz) (`variants/gi1_dp/`); CU idx5 LUT fork pending.

---

## 1. Design rules

1. **ALU A:** `q_a` ← **R0** only (CPLD-DP).
2. **ALU B:** **`net_mbr[7:0]`** from MBR 574 → `net_b[7:0]` — **not** from CPLD `q_b`.
3. **Write target:** **`reg_we` → R0** only (implicit in DP; no `w_sel` on G-IC).
4. **Phase FSM** on CPLD-CU only; **no Flash param fetch**; Flash `$4000` **unused**.
5. **idx5 decode:** FSM key `(opcode[4:0] << 2) | phase[1:0]` — **128 slots** on CU.
6. **Strobes:** CU drives **14 nets directly** to SoC (no external CW latch).
7. **Branch:** `PC_LOAD_EN = macro_end & lut_pc_load & (!lut_pc_flg_z | FLG_Z)` on CU.
8. **TFR:** **Removed** — `0x10–0x1F` trap/NOP; no `tfr_valid` comb.
9. **Mailbox, MAP, `/CE`** — outside CPLD.

---

## 2. CPLD-CU port list

### Inputs (7)

| Signal | Source | Role |
|--------|--------|------|
| `OPC[4:0]` | IR574 | idx5 FSM |
| `FLG_Z` | FLG574 | BEQ @ macro_end |
| `CLK` | 2 MHz | Phase FSM |

### Outputs — SoC (14)

| Signal | Function |
|--------|----------|
| `MEM_RD`, `MEM_WR` | Memory strobes |
| `Y_OE` | Bus drive (STA, ADD ph2 writeback) |
| `FLG_WE` | Flag latch write |
| `PC_LOAD_EN` | Branch commit |
| `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1` | ALU controls |

`bctrl1`/`bctrl3` fan out at 153 from `bctrl0`/`bctrl2`.

### Outputs — G-IC to CPLD-DP (1)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write (LUT only → R0) |

**Pin budget (desk):** ~21/32 used (~11 spare).

---

## 3. CPLD-DP port list

### Inputs (9)

| Signal | Source | Role |
|--------|--------|------|
| `d_in[7:0]` | Data bus | LDA / ALU writeback |
| `reg_we` | CPLD-CU G-IC | R0 write strobe |
| `CLK` | 2 MHz | R0 FF clock |

### Outputs (8)

| Signal | Function |
|--------|----------|
| `q_a[7:0]` | Async read → ALU A |

**No `q_b`.** ALU B from **MBR 574** off-chip.

**Pin budget (desk):** **17/32** used (15 spare).

---

## 4. G-IC bundle

| ID | Signal | DP pin (desk) |
|----|--------|---------------|
| G01 | `reg_we` | 12 |

**CLK:** pin 43 both chips (parallel).

Detail: [cpld-dual-routing.md](cpld-dual-routing.md)

---

## 5. TFR (removed)

Register-to-register implied moves (`0x11–0x19`) are **not** implemented in v1.0 Gi1. Prior rev G behavior: [archive/rev-g-normative-snapshot/reference/hardware/cpld-system-controller.md](../../archive/rev-g-normative-snapshot/reference/hardware/cpld-system-controller.md) §5.

Software uses **RAM** for additional variables (AC-centric model).

---

## 6. JTAG / programming

Daisy chain: programmer → **CU (TDI first)** → **DP** → programmer TDO.  
TCK/TMS paralleled. See [cpld-dual-jtag.md](cpld-dual-jtag.md).

---

## 7. ADD / CMP ph1 policy (Gi1)

For ALU_REG templates, **ph1 does not assert REG_WE** — imm8 operand is held in **MBR 574** and routed to ALU B. **ph2** asserts `REG_WE` → **R0** for ADD; CMP ph2 asserts **FLG_WE** only.

**MBR hold:** Do not reload MBR operand byte during ALU_REG macro ([M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md)).

---

## 8. MC / fit gate

| Chip | Desk estimate | Gate |
|------|---------------|------|
| CPLD-CU | ~24–30 MC | WinCUPL Design fits |
| CPLD-DP | ~10–18 MC | WinCUPL Design fits |

Do not record fitter used-MC counts as normative BOM gates — **Design fits** is the bring-up gate.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | **Gi1 v1.0** — R0 only; G-IC 1-wire; MBR→ALU B |
| 2026-07-06 | **rev G** archived |
| 2026-07-06 | Tier C monolithic spec archived |
