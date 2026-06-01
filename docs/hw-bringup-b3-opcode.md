# B3 — opcode → control line cheat sheet

Breadboard **DIP / tie** settings for 12 `alu_op[3:0]` operations (v0.2 CW `[15:12]`). Generated from the same vectors as [`alu8_full.yaml`](../hw/tests/alu8_full.yaml).

Regenerate: `python tools/gen_opcode_cheatsheet.py`

**Netlist has no `alu_sel` bus** — in Phase1 hwsim use [`alu_decode.yaml`](../hw/netlist/blocks/alu_decode.yaml) or set each control net manually (or hardwire per row).

INC/DEC: do **not** drive `net_b0..7`; use `153_B` sel (`b_const_sel`, `b_sel`) — see [alu8.md](../hw/netlist/blocks/alu8.md).

## Control nets (quick ref)

| Net | Role |
|-----|------|
| `net_cin` | 283 carry in (1 for SUB/CMP) |
| `net_b_sel` | 153_B LSB: 0=B, 1=~B |
| `net_b_const_sel` | 153_B MSB: 1 → INC/DEC constant mux |
| `net_cmp_z`, `net_cmp_c_ge` | SUB-derived CMP flags (`Y==0`, `net_c_hi`) |
| `net_153_s0/s1` | Logic enable → `157_YBP` selects `net_y_logic` |
| `net_lgc0..3` | Gigatron 153 C0..C3 (from decode or DIP) |

## 12 opcodes

| sel | `alu_op` | Op | A | B | cin | b_sel | b_cst | s1 | s0 | lgc | b_hi | Y | Y LEDs y7..y0 | Fixed ties |
|-----|----------|-----|---|---|-----|-------|-------|----|----|-----|------|---|---------------|------------|
| 0 | `0` | **NOP** | `00` | `00` | 0 | 0 | 0 | 0 | 0 | `0000` | 0 | `00` | `00000000` | GND: cin, 153_s0, 153_s1, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2, lgc3 |
| 1 | `1` | **ADD** | `12` | `34` | 0 | 0 | 0 | 0 | 0 | `0000` | 0 | `46` | `01000110` | GND: cin, 153_s0, 153_s1, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2, lgc3 |
| 2 | `2` | **SUB** | `12` | `34` | 1 | 1 | 0 | 0 | 0 | `0000` | 0 | `DE` | `11011110` | GND: 153_s0, 153_s1, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2, lgc3; VCC: cin, b_sel |
| 3 | `3` | **AND** | `12` | `34` | 0 | 0 | 0 | 0 | 1 | `1000` | 0 | `10` | `00010000` | GND: cin, 153_s1, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2; VCC: 153_s0, lgc3 |
| 4 | `4` | **OR** | `12` | `34` | 0 | 0 | 0 | 1 | 0 | `1110` | 0 | `36` | `00110110` | GND: cin, 153_s0, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0; VCC: 153_s1, lgc1, lgc2, lgc3 |
| 5 | `5` | **XOR** | `12` | `34` | 0 | 0 | 0 | 1 | 1 | `0110` | 0 | `26` | `00100110` | GND: cin, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc3; VCC: 153_s0, 153_s1, lgc1, lgc2 |
| 6 | `6` | **NOT** | `12` | `00` | 0 | 0 | 0 | 1 | 1 | `0001` | 0 | `ED` | `11101101` | GND: cin, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc1, lgc2, lgc3; VCC: 153_s0, 153_s1, lgc0 |
| 7 | `7` | **PASS_A** | `12` | `FF` | 0 | 0 | 0 | 0 | 1 | `1000` | 0 | `12` | `00010010` | GND: cin, 153_s1, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2; VCC: 153_s0, lgc3 |
| 8 | `8` | **PASS_B** | `FF` | `34` | 0 | 0 | 0 | 0 | 1 | `1000` | 0 | `34` | `00110100` | GND: cin, 153_s1, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2; VCC: 153_s0, lgc3 |
| 9 | `9` | **INC** | `12` | `00` | 0 | 0 | 1 | 0 | 0 | `0000` | 0 | `13` | `00010011` | GND: cin, 153_s0, 153_s1, b_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2, lgc3; VCC: b_const_sel |
| 10 | `A` | **DEC** | `12` | `00` | 0 | 1 | 1 | 0 | 0 | `0000` | 1 | `11` | `00010001` | GND: cin, 153_s0, 153_s1, lgc0, lgc1, lgc2, lgc3; VCC: b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7 |
| 11 | `B` | **CMP** | `12` | `34` | 1 | 1 | 0 | 0 | 0 | `0000` | 0 | `DE` | `11011110` | GND: 153_s0, 153_s1, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7, lgc0, lgc1, lgc2, lgc3; VCC: cin, b_sel |

Columns: **b_cst** = `net_b_const_sel`, **lgc** = `net_lgc3..0` (Gigatron C inputs), **b_hi** = `net_b_const_bit1..7` (same value), **Y LEDs** = MSB left (y7) … LSB (y0).

## Smoke vectors (B3a first)

| Op | A | B | Expected Y |
|----|---|---|------------|
| SUB | 0x12 | 0x34 | 0xDE |
| XOR | 0x12 | 0x34 | 0x26 |
| INC | 0x12 | — | 0x13 |

See phased bring-up: [hw-bringup-b3.md](hw-bringup-b3.md).
