# P1M1 FSM and ISA delta

**Parent:** [README.md](README.md)  
**Normative ISA:** [reference/hardware/microcode-spec.md](../../../reference/hardware/microcode-spec.md) — unchanged in this folder

---

## 1. User-visible ISA

| Aspect | rev G | P1M1 |
|--------|-------|------|
| Opcode encoding | unchanged | unchanged |
| Mnemonic (e.g. `ADD #imm`) | unchanged | unchanged |
| **Macro duration** | ph2 = 250 ns | ph2 = **500 ns** (2× half-cycle) |

Programmer sees **slower** ADD/CMP execute phase; no new instructions required for P1M1 desk model.

---

## 2. rev G ADD (reference)

| Phase | Duration | Key strobes |
|-------|----------|-------------|
| ph0 | 250 ns | `Y_OE`, fetch imm |
| ph1 | 250 ns | `REG_WE` → R1 (imm) |
| ph2 | 250 ns | ALU; `REG_WE` → R2; `FLG_WE` |

Fixed operands: R0 + R1 → R2 ([microcode-spec.md](../../../reference/hardware/microcode-spec.md) §4).

---

## 3. P1M1 ADD (desk)

| Phase | 2M half | Strobes |
|-------|---------|---------|
| ph0 | 1× | unchanged |
| ph1 | 1× | `REG_WE` → R1 |
| **ph2a** | half 0 (0–250 ns) | `r_sel_a`/`r_sel_b` on G-IC; DP `op_fetch=1`; TDM; **no** `REG_WE`/`FLG_WE` |
| **ph2b** | half 1 (250–500 ns) | ALU `cin`/`bctrl`/`lgc`/`s0`/`s1`; **`REG_WE` → R2**; **`FLG_WE`** @ 500 ns |

### `r_sel` programming (4-GPR ADD example)

| Port | rev G | P1M1 ph2a |
|------|-------|-----------|
| A | fixed R0 | `r_sel_a` = 00 |
| B | fixed R1 | `r_sel_b` = 01 |
| Result | fixed R2 | `w_sel` = 10 @ ph2b |

Generalized ADD (future ISA): `r_sel` from extended microcode row.

---

## 4. CU implementation options

| ID | Method | idx5 rows | Notes |
|----|--------|-----------|-------|
| **F-A** | Split **ph2a** / **ph2b** LUT entries | +1 row per ALU op | Clearest timing story |
| **F-B** | **ph2 stretch** counter on CU | same slot count | Internal 0/1 sub-phase |
| **F-C** | DP `op_fetch` autotoggle every `clk_sys` while `alu_exec` pin | minimal CU | Needs `alu_exec` G-IC |

Research default: **F-A** or **F-B** documented; PLD uses local `op_fetch` toggle.

---

## 5. CMP and flags-only

| | ph2b @ 500 ns |
|---|----------------|
| CMP | `FLG_WE` only (no `REG_WE` → R2) — same policy as rev G ph2 flags_only |

---

## 6. MEM_LD / MEM_ST / TFR

| Template | P1M1 impact |
|----------|-------------|
| MEM_LD | No operand TDM; unchanged |
| MEM_ST | STR path may use `r_sel` + `Y_OE`; no dual 574 |
| TFR | G-IC xfer; no ALU half stretch |

Operand TDM + dual 574 applies to **ALU_REG** templates (ADD, CMP).

---

## 7. P1M1 vs M2

| | **P1M1** | **M2** |
|---|----------|--------|
| Goal | 500 ns execute with latched A/B | 500 ns execute |
| Means | **574×2** + ph2 stretch | **FSM row split** (can omit 574 B if P1 live-B) |
| Hardware | Defining feature | Optional |
| ISA cycle | 500 ns ph2 | 500 ns ph2 |

P1M1 **implies** M2-style duration; difference is **explicit latch hardware** making timing closure obvious on scope.

---

## 8. cyclesim / bring-up (future)

- CU LUT: ph2a/ph2b rows or stretch bit
- DP: `op_fetch` gates `q_bus` mux ([p1m1_dp PLD](../variants/p1m1_dp/system_ctrl.pld))
- Test: ADD @ 2 MHz with `r_sel_a=0`, `r_sel_b=1` → R2

---

## Related

- [architecture.md](architecture.md)
- [timing-closed.md](timing-closed.md)
