# 8-bit ALU block (`alu8.yaml`)

BOM **20** 74HC IC (hwsim **52** gate-level instances), 12 `alu_sel` operations per [microcode-spec](../../../archive/verilog-sim/docs/microcode-spec.md).

Integrated with 574: [`alu_b3.yaml`](alu_b3.yaml) · bring-up: [`docs/hw-bringup-b3.md`](../../../docs/hw-bringup-b3.md).

## IC map (physical)

| Ref prefix | Part | Qty | Role |
|------------|------|-----|------|
| `U_ALU_283_LO/HI` | 74HC283 | 2 | 8-bit ripple adder |
| `U_ALU_153_0..3` | 74HC153 | 4 | Per-bit 4:1 output MUX (sum/and/or/xor-or-not) |
| `U_ALU_86_INV_*` | 74HC86 | 2 (8 gates) | `B[i] XOR sub_en` for subtract |
| `U_ALU_86_XOR_*` | 74HC86 | 2 (8 gates) | `A[i] XOR B[i]` for XOR op |
| `U_ALU_08_*`, `U_ALU_32_*` | 74HC08/32 | 2 each | 8-bit AND / OR |
| `U_ALU_04_N*` | 74HC04 | 2 (8 inv) | 8-bit NOT (~A) |
| `U_ALU_157_B_*` | 74HC157 | 2 | Stage-1: register B vs ~B |
| `U_ALU_157_B2_*` | 74HC157 | 2 | Stage-2: path vs INC/DEC constant → `net_b_add*` |
| `U_ALU_157_OUT_*` | 74HC157 | 2 | XOR vs ~A into 153 C3 |

Regenerate netlist: `python tools/gen_alu8_netlist.py`

## Control nets (VLIW / test stimulus)

| Net | Role |
|-----|------|
| `net_a0..7`, `net_b0..7` | Operands (B register; INC/DEC use cascade, not direct B drive) |
| `net_sub_en` | 1 → invert B through `86_INV` |
| `net_cin` | 283 cascade carry in |
| `net_b_sel` | 157 B stage-1: 0=B, 1=~B |
| `net_b_const_sel` | 157 B2: 0=path, 1=INC/DEC constant pattern |
| `net_b_const_bit1..7` | INC=0, DEC=1 (bit0 tied VCC in netlist) |
| `net_b_add0..7` | 283 B inputs (after B2 cascade) |
| `net_153_s0/s1` | Output MUX select (00=sum, 01=and, 10=or, 11=C3) |
| `net_c3_sel` | 157 OUT: 0=xor on C3, 1=~A on C3 (NOT) |

## `alu_sel` → control (block tests)

| sel | Op | sub | cin | b_sel | b_const_sel | s1:s0 | c3_sel | B into adder |
|-----|-----|-----|-----|-------|-------------|-------|--------|--------------|
| 0 | NOP | 0 | 0 | 0 | 0 | 00 | 0 | 0 |
| 1 | ADD | 0 | 0 | 0 | 0 | 00 | 0 | B |
| 2 | SUB | 1 | 1 | 1 | 0 | 00 | 0 | ~B |
| 3 | AND | 0 | 0 | 0 | 0 | 01 | 0 | — |
| 4 | OR | 0 | 0 | 0 | 0 | 10 | 0 | — |
| 5 | XOR | 0 | 0 | 0 | 0 | 11 | 0 | — |
| 6 | NOT | 0 | 0 | 0 | 0 | 11 | 1 | — |
| 7 | PASS_A | 0 | 0 | 0 | 0 | 01 | 0 | B=0xFF |
| 8 | PASS_B | 0 | 0 | 0 | 0 | 01 | 0 | A=0xFF |
| 9 | INC | 0 | 0 | 0 | **1** | 00 | 0 | **0x01** via B2 |
| 10 | DEC | 0 | 0 | 0 | **1** | 00 | 0 | **0xFF** via B2 |
| 11 | CMP | 1 | 1 | 1 | 0 | 00 | 0 | ~B |

PASS uses AND with `0xFF` mask; SUB borrow flag is `~carry_hi` (see microcode C flag).

## Critical paths (hwsim @ max, bit0)

| Opcode | Path (ref.pin hops) |
|--------|---------------------|
| **SUB** | `86_INV_0.A` → `Y` → `157_B_0.1B` → `1Y` → `157_B2_0.1A` → `1Y` → `283_LO.B0` → `C4` → `283_HI.C4` → `153_0.1C0` → `1Y` |
| **XOR** | `86_XOR_0.A` → `Y` → `157_OUT_0.4A` → `4Y` → `153_0.1C3` → `1Y` |

Output-pin delay sum @ max: SUB **~169 ns**, XOR **~76 ns** (within 250 ns @ 2 MHz typ).

## Tests

```bash
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/alu8_timing.yaml
python -m hwsim run hw/tests/alu_b3_sub_critical.yaml
python -m hwsim run hw/tests/alu_b3_xor_critical.yaml
python -m hwsim run hw/tests/alu_b3_latch.yaml
python -m hwsim run hw/tests/alu_b3_inc_dec.yaml
```

Sub-block adder only: [`alu283.yaml`](alu283.yaml).

## BOM delta

See [BOM.md](../../../BOM.md) — +2×86, +4×157 (B/OUT/B2), +2×04 vs original 12-IC ALU; system **50** core IC.
