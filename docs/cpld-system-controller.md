# CPLD System Controller v1.0

**Device:** ATF1504AS (**100-TQFP**) · **Role:** **GPR only** (R0–R3)  
**CE tree:** 74HC138×2 + 08/32/04 · **Reg_Sel:** Flash CW B9–B8  
**GPR timing:** [archive/pre-v0.1/cpld-hybrid-v1.3.md](archive/pre-v0.1/cpld-hybrid-v1.3.md)

**Bring-up:** [hw-bringup/README.md](hw-bringup/README.md) · [breadboard-wiring.md](hw-bringup/breadboard-wiring.md)

**CPLD bitstream:** draft until MC fit report — target **≤40 MC** on **ATF1504** only.

---

## 1. Design rules

1. **GPR storage** inside ATF1504 — async dual read `q_a`/`q_b`; sync write on `REG_WE` ∧ CLK↑ with `w_sel` from CW.
2. **`REG_SEL[1:0]`** latched from CW — **not** decoded from opcode×phase inside CPLD.
3. **Mailbox, MAP, `/CE`** — **outside** CPLD (08/32/04 + 138×2).
4. **Bus control** (MEM_RD/WR, Y_OE) — CW latch **direct** to 245/Flash; not buffered in CPLD.
5. **RESET `$FFFC`** — 157 address MUX (recommended) or minimal CPLD comb stub.

**hwsim:** `CPLD_REGFILE` + `CPLD_GPR_CTRL` + `MEM_DECODE_BREADBOARD`.

---

## 2. Port list

### Inputs

| Signal | Source |
|--------|--------|
| `REG_SEL[1:0]` | CW latch B9–B8 |
| `REG_WE` | CW latch B3 |
| `d_in[7:0]` | Data bus (GPR write) |
| `CLK` | System clock (GPR write edge) |
| `R_SEL_A[1:0]`, `R_SEL_B[1:0]` | CW/context (same as REG_SEL per phase) |

### Outputs

| Signal | Function |
|--------|----------|
| `q_a[7:0]`, `q_b[7:0]` | Async read → ALU A/B |
| `w_sel[1:0]` | Internal write address when REG_WE |

**No** `A[15:0]`, `opcode`, `phase`, `MAILBOX_EN`, `/CE`, or bus mux outputs on CPLD.

---

## 3. GPR write

```vhdl
w_sel <= REG_SEL when REG_WE = '1' else "00";
-- FF write @ CLK↑
```

`REG_SEL` per opcode×phase is packed in Flash — see [microcode-spec.md](microcode-spec.md).

---

## 4. CE / mailbox (off-chip)

```text
A[15:0] ──► 08/32 (MAILBOX_EN, MAP×A11)
         ──► 74HC138 #2 (half-select)
         ──► 74HC138 #1 (CBA = A15,A14,A13)  E: !MAILBOX_EN
         ──► 08/32/04 ──► RAM1_CS, RAM2_CS, ROM_CS
```

Truth: [memory-map.md](memory-map.md) · [`decode_ce_breadboard()`](../hw/logic/cpld_decode.py).

---

## 5. Physical layout

- **74HC138×2** adjacent to SRAM/Flash — short `/CE` stubs.
- **08/32** glue next to 138 — mailbox/MAP fan-in.
- **0.1 µF×4** at ATF1504 TQFP.
- Optional **22–33 Ω** on `q_a`/`q_b`.
- **574×2** CW_L/CW_H near Flash data bus.

---

## 6. Macrocell budget

| Function | Est. MC |
|----------|---------|
| GPR 32 FF + read mux | ~32 |
| `w_sel` mux + clock enable | ~4–8 |
| **Total** | **~36–40** |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-10 | **v1.0** — GPR-only CPLD; Reg_Sel→CW; CE→138×2+gates |
