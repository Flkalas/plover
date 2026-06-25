# 8-bit ALU block (`alu8.yaml`)

BOM **14** 74HC DIP IC (hwsim **~28** instances + behavioral glue), 12 `alu_sel` operations per [microcode-spec](../../../docs/normative/hardware/microcode-spec.md).

**Phase A/B1:** `153_B` B-path MUX · 산술 Y **`157_YBP`** (sum bypass).  
**Phase B2:** Gigatron **`153_L`** — **08/32/86/04_N/157_OUT 제거**.  
**CMP flags:** **`ALU_CMP_SUB`** — `net_cmp_z` = (`net_y==0`), `net_cmp_c_ge` = `net_c_hi` (no **74HC85** on breadboard).

Integrated with 574: [`alu_b3.yaml`](alu_b3.yaml) · design: [`docs/normative/hardware/alu8-phase-b.md`](../../../docs/normative/hardware/alu8-phase-b.md) · bring-up: [`docs/normative/hw-bringup/alu8-assembly-spec.md`](../../../docs/normative/hw-bringup/alu8-assembly-spec.md).

## IC map (physical)

| Ref prefix | Part | Qty | Role |
|------------|------|-----|------|
| `U_ALU_283_LO/HI` | 74HC283 | 2 | 8-bit ripple adder |
| `U_ALU_153_B_0..3` | 74HC153 | 4 | B-path 4:1: B, ~B, INC `0x01`, DEC `0xFF` |
| `U_ALU_153_L_0..3` | 74HC153 | 4 | Gigatron logic (mux1/mux2 → bits 2n, 2n+1) |
| `U_ALU_157_YBP_*` | 74HC157 | 2 | Arith bypass: sum vs `net_y_logic` → `net_y` |
| `U_ALU_Y_MUX_SEL` | *(behavioral)* | 1 | `net_y_mux_sel` = `153_s0 \| 153_s1` |
| `U_ALU_04_BINV_*` | 74HC04 | 8 (gates) | `~B[i]` for 153_B C1 |
| `U_ALU_CMP_SUB` | *(behavioral)* | 1 | CMP Z/C_GE from SUB result (no 7485) |

Breadboard: eight hwsim `ALU_153_SLICE` refs map to **four** 74HC153 DIP (one active mux per pair) — see [`docs/normative/hardware/alu8-phase-b.md`](../../../docs/normative/hardware/alu8-phase-b.md).

Regenerate:

```bash
python tools/gen_alu_decode_netlist.py
python tools/gen_alu8_netlist.py
```

## B-path select (`153_B`)

`A` = `net_b_sel`, `B` = `net_b_const_sel` → `sel = b_sel | (b_const_sel<<1)`:

| sel | `b_const_sel` | `b_sel` | Input |
|-----|---------------|---------|--------|
| 0 | 0 | 0 | B |
| 1 | 0 | 1 | ~B |
| 2 | 1 | 0 | INC (`C2`: bit0=1, else 0) |
| 3 | 1 | 1 | DEC (`C3`: all 1) |

SUB/CMP: `b_sel=1`, `cin=1` (no `net_sub_en`).

## Gigatron logic (`153_L`)

Per bit: `sel = net_a[i] | (net_b[i]<<1)`; `C0..C3` = `net_lgc0..3` from decode ([`alu_decode.yaml`](alu_decode.yaml)) or test stimulus.

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
| `net_cmp_z` | **Y == 0** after SUB/CMP (`b_sel=1`, `cin=1`) |
| `net_cmp_c_ge` | **`net_c_hi`** from 283 (unsigned A≥B) |

Test: [`alu8_cmp_sub.yaml`](../../tests/alu8_cmp_sub.yaml).

## Control nets

| Net | Role |
|-----|------|
| `net_lgc0..3` | 153_L constant inputs (Gigatron) |
| `net_153_s0/s1` | Logic enable → `157_YBP` |
| `net_b_sel`, `net_b_const_sel`, `net_cin` | B-path / carry |

## Critical paths (hwsim @ max, bit0)

| Opcode | Path | max (ns) |
|--------|------|----------|
| **SUB / CMP** | `net_b0` → `04_BINV` → `153_B` → `283` → `157_YBP` | **151** |
| **ADD / INC** | `283` → `157_YBP` | **108** |
| **AND / OR / XOR / NOT / PASS** | `153_L` → `157_YBP` | **46** |

## Tests

```bash
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/alu8_opcode_timing.yaml
python -m hwsim run hw/tests/alu8_cmp_sub.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
```

Vectors: [`tools/alu8_cases.py`](../../../tools/alu8_cases.py)

## BOM

[ BOM.md](../../../BOM.md) — ALU **14** DIP IC · [bom-maintenance.md](../../../docs/developer/project/bom-maintenance.md) — 검산/이력.
