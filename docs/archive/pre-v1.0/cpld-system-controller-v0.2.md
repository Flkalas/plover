# CPLD System Controller v0.2

**Device:** ATF1504AS (**100-TQFP** target) · **Role:** GPR (R0–R3) + comb decode glue + Reg_Sel  
**GPR ports:** [cpld-hybrid-v1.3.md](archive/pre-v0.1/cpld-hybrid-v1.3.md) · **CE tree:** 74HC138×2 + 08/32/04

**Bring-up:** [hw-bringup/tier2-migration.md](hw-bringup/tier2-migration.md) · Tier 0 legacy: [cpld-system-controller-v0.1.md](archive/pre-v0.1/cpld-system-controller-v0.1.md)

**CPLD bitstream:** draft until MC fit report (escape: **ATF1508** if > 64 MC).

---

## 1. Design rules

1. **No state registers** for reset, map mode, or boot FSM.
2. **MAP_MODE** and **RESET_N** are inputs — map changes only via operator hardware.
3. Bus phase (φ1/φ2) from **74HC74** — CPLD combines with gates only.
4. **GPR storage** is **inside ATF1504** — async dual read `q_a`/`q_b`; sync write on `REG_WE` ∧ CLK↑ with internal `w_sel`.
5. **Final RAM/ROM `/CE`** from **74HC138×2 + glue** — CPLD drives mailbox, MAP×A11 qualifiers, and 138 enables only.

**hwsim:** `CPLD_REGFILE` + `CPLD_SYSTEM_CTRL_TIER2` (`t_pd=0` comb). Tier 0 tests use `CPLD_SYSTEM_CTRL` + `REGFILE_574_GPR`.

---

## 2. Port list (draft)

### Inputs

| Signal | Source |
|--------|--------|
| `RESET_N` | Reset button / POR |
| `MAP_MODE` | DIP switch (0=Boot, 1=Run) |
| `A[15:0]` | Address bus |
| `opcode[3:0]` | From IR/MBR during execute |
| `phase[1:0]` | Phase counter |
| `REG_WE` | Flash CW bit B3 |
| `phi_cpu`, `phi_cop` | Clock divider |
| `d_in[7:0]` | Write data (GPR) |
| `CLK` | System clock (GPR write edge) |

### Outputs — GPR

| Signal | Function |
|--------|----------|
| `q_a[7:0]`, `q_b[7:0]` | Async read ports → ALU A/B |
| `w_sel[1:0]` | Internal write address (from Reg_Sel when REG_WE) |
| `r_sel_a[1:0]`, `r_sel_b[1:0]` | Read port selects (from micro-sequence / CW context) |

### Outputs — map / CE glue

| Signal | Function |
|--------|----------|
| `mailbox_en` | `$FF00–$FFFB` |
| `addr_override_fffc` | Force fetch addr on reset |
| `138_half_en` | Enable 138 #2 (A15 half-select, MAP-qualified) |
| `138_coarse_en` | Enable 138 #1 (gated by `!MAILBOX_EN`) |
| `map_a11_qual` | Mode A boot ROM window glue (A11 + MAP) |

Final **`RAM1_CS_N`**, **`RAM2_CS_N`**, **`ROM_CS_N`** = 138 Y* + 08/32/04 (see [memory-map.md](memory-map.md) §2.1).

### Outputs — bus (unchanged)

| Signal | Function |
|--------|----------|
| `bus_dir`, `bus_oe` | 245 / CPU vs RP2350 |
| `y_oe`, `mem_rd`, `mem_wr` | From CW bits (buffered) |

**No `LOAD_R0..3`** in v0.2 — external 574 GPR removed.

---

## 3. Mailbox decode

```
MAILBOX_EN = (A >= 16'hFF00) && (A <= 16'hFFFB)
```

Never assert for `$FFFC–$FFFF`. Implemented in CPLD; gates 138 enables.

---

## 4. CE partition (138×2 + glue)

CPLD owns **mailbox**, **reset `$FFFC`**, **MAP×A11** boot window. Coarse regions via 138:

```text
A[15:0] ──► 138 #2 (half: A15 / MAP)
         ──► 138 #1 (CBA = A15,A14,A13)  E: !MAILBOX_EN
         ──► 08/32/04 ──► RAM1_CS, RAM2_CS, ROM_CS
```

Truth table: [memory-map.md](memory-map.md) · reference logic: [`hw/logic/cpld_decode.py`](../hw/logic/cpld_decode.py) `decode_ce_tier2()`.

---

## 5. Reset — hardwired `$FFFC`

When `RESET_N` active (low): comb mux forces **fetch address `$FFFC`**. No boot counter inside CPLD.

---

## 6. GPR write decode

`Reg_Sel[1:0]` = comb `{opcode[3:0], phase[1:0]}` (see [microcode-spec.md](microcode-spec.md)).

```vhdl
w_sel <= Reg_Sel when REG_WE = '1' else "00";  -- internal FF write @ CLK↑
```

---

## 7. Physical layout

- Place **74HC138×2 adjacent to SRAM/Flash** — short `/CE` stubs (star from 138, not CPLD).
- **0.1 µF×4** at ATF1504 TQFP power pins.
- Optional **22–33 Ω** on `q_a`/`q_b` if SSO scope shows ring.
- **574×1 FLG** near ALU CMP outputs.

---

## 8. Macrocell budget (target — tight)

| Function | Est. MC |
|----------|---------|
| GPR 32 FF + read mux | ~32 |
| Reg_Sel PLA | ~24 |
| Mailbox + `$FFFC` + MAP glue | ~12 |
| 138 enables + bus mux | ~8 |
| **Total** | **~76** → **ATF1508** if 1504 overflow |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | v0.1 — external 574 GPR, CPLD direct CS (archived) |
| 2026-06-10 | **v0.2** — CPLD GPR + 138×2 CE offload; 100-TQFP; no GAL |
