# 8-bit ALU block (`alu8.yaml`)

BOM **12** 74HC DIP IC, 12 `alu_op` operations per [microcode-spec](../../../docs/normative/hardware/microcode-spec.md).

**Architecture:** pure Gigatron **B_CTRL** bit-slice — `U_ALU_153_0..7` (mux1=logic, mux2=`bctrl*`) with operands on shared A/B select; **`ALU_INC_B_SEL`** + **`ALU_INC_2C2`** glue for INC only.  
**CMP flags:** **`ALU_CMP_SUB`** — `net_cmp_z` = (`net_y==0`), `net_cmp_c_ge` = `net_c_hi` (no **74HC85** on breadboard).

Integrated with 574: [`alu_b3.yaml`](alu_b3.yaml) · design: [`docs/normative/hardware/alu8-phase-b.md`](../../../docs/normative/hardware/alu8-phase-b.md) · bring-up: [`docs/normative/hw-bringup/alu8-assembly-spec.md`](../../../docs/normative/hw-bringup/alu8-assembly-spec.md).

## IC map (physical)

| Ref prefix | Part | Qty | Role |
|------------|------|-----|------|
| `U_ALU_283_LO/HI` | 74HC283 | 2 | 8-bit ripple adder |
| `U_ALU_153_0..7` | 74HC153 | 8 | Bit-slice: mux1 logic + mux2 B_CTRL |
| `U_ALU_157_YBP_*` | 74HC157 | 2 | Arith bypass: sum vs `net_y_logic` → `net_y` |
| `U_ALU_INC_B_SEL` | *(behavioral)* | 1 | INC: force 153 B-select = 1 |
| `U_ALU_INC_2C2` | *(behavioral)* | 1 | INC: per-bit 153 `2C2` override |
| `U_ALU_Y_MUX_SEL` | *(behavioral)* | 1 | `net_y_mux_sel` = `153_s0 \| 153_s1` |
| `U_ALU_CMP_SUB` | *(behavioral)* | 1 | CMP Z/C_GE from SUB result (no 7485) |

Regenerate:

```bash
python tools/gen_alu_decode_netlist.py
python tools/gen_alu8_netlist.py
```

## Per-bit 153 (`U_ALU_153_i`)

| Mux | Connection |
|-----|------------|
| mux1 | `1C0..3` = `net_lgc0..3`, `1Y` = `net_y_logic[i]`, `1G` = GND |
| mux2 | `2C0..3` = `net_bctrl0..3` (via `net_153_2c2[i]` for `2C2`), `2Y` = `net_b_add[i]`, `2G` = GND |
| A/B | `A` = `net_a[i]`; `B` = `net_b153_sel[i]` ← `ALU_INC_B_SEL` |

Select (both muxes): `sel = A | (B<<1)` on pins 14 / 2.

## B_CTRL (`net_bctrl3..0` → mux2 `2C3..2C0`)

| Opcode | bctrl[3:0] | mux2 behaviour |
|--------|------------|----------------|
| **ADD** | `1100` | B[i] pass |
| **SUB/CMP** | `0011` | ~B[i] (no 04) |
| **DEC** | `1111` | constant 1 |
| **INC** | *(don’t care)* | `inc_en=1` + per-bit `2C2` glue + B forced high |

SUB/CMP: `bctrl=(1,1,0,0)`, `cin=1`.

## Gigatron logic (mux1)

Per bit in logic mode: `sel = net_a[i] | (net_b[i]<<1)`; `1C0..3` = `net_lgc0..3`.

| Pattern `lgc3:0` | Op |
|------------------|-----|
| `0001` | AND, PASS_A/B |
| `0111` | OR |
| `0110` | XOR |
| `1000` | NOT (B=0 in vectors) |

`net_153_s0/s1` → `net_y_mux_sel` → **157_YBP** picks sum vs logic.

## CMP (SUB-derived flags)

| Flag | Source (breadboard) |
|------|---------------------|
| `net_cmp_z` | **Y == 0** after SUB/CMP (`bctrl` SUB pattern, `cin=1`) |
| `net_cmp_c_ge` | **`net_c_hi`** from 283 (unsigned A≥B) |

Test: [`alu8_cmp_sub.yaml`](../../tests/alu8_cmp_sub.yaml).

## Control nets

| Net | Role |
|-----|------|
| `net_lgc0..3` | mux1 data (Gigatron) |
| `net_bctrl0..3` | mux2 data (B_CTRL) |
| `net_inc_en` | INC glue enable |
| `net_153_s0/s1` | Logic enable → `157_YBP` |
| `net_cin` | 283 carry in |

## Critical paths (pre-flight sim @ max, bit0)

| Opcode | Path | max (ns) |
|--------|------|----------|
| **SUB / CMP** | `net_b0` → `U_ALU_153_0.B` → `2Y` → `283` → `157_YBP` | **~133** |
| **ADD / INC** | `283` → `157_YBP` | **108** |
| **AND / OR / XOR / NOT / PASS** | `U_ALU_153_0.1Y` → `157_YBP` | **46** |

## Tests

```bash
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/alu8_opcode_timing.yaml
python -m hwsim run hw/tests/alu8_cmp_sub.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
```

Vectors: [`tools/alu8_cases.py`](../../../tools/alu8_cases.py)

## BOM

[BOM.md](../../../BOM.md) — ALU **12** DIP IC · [bom-maintenance.md](../../../docs/developer/project/bom-maintenance.md) — 검산/이력.
