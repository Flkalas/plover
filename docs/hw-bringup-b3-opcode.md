# B3 — opcode → control line cheat sheet

Breadboard **DIP / tie** settings for 12 `alu_sel` operations. Generated from the same vectors as [`alu8_full.yaml`](../hw/tests/alu8_full.yaml).

Regenerate: `python tools/gen_opcode_cheatsheet.py`

**Netlist has no `alu_sel` bus** — set each control net manually (or hardwire per row).

INC/DEC: do **not** drive `net_b0..7`; use `b_const_sel` + `b_const_bit1..7` only.

## Control nets (quick ref)

| Net | Role |
|-----|------|
| `net_sub_en` | 1 → invert B (SUB/CMP) |
| `net_cin` | 283 carry in (1 for SUB/CMP) |
| `net_b_sel` | 157 stage-1: 0=B, 1=~B |
| `net_b_const_sel` | 157 B2: 0=path, 1=INC/DEC constant |
| `net_b_const_bit1..7` | INC=0, DEC=1 (bit0 = VCC in netlist) |
| `net_153_s0/s1` | Output MUX: 00=sum, 01=and, 10=or, 11=C3 |
| `net_c3_sel` | 157 OUT: 0=XOR path, 1=~A (NOT) |

## 12 opcodes

| sel | Op | A | B | sub | cin | b_sel | b_cst | s1 | s0 | c3 | b_hi | Y | Y LEDs y7..y0 | Fixed ties |
|-----|-----|---|---|-----|-----|-------|-------|----|----|----|------|---|---------------|------------|
| 0 | **NOP** | `00` | `00` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `00` | `00000000` | GND: sub_en, cin, 153_s0, 153_s1, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7 |
| 1 | **ADD** | `12` | `34` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `46` | `01000110` | GND: sub_en, cin, 153_s0, 153_s1, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7 |
| 2 | **SUB** | `12` | `34` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | `DE` | `11011110` | GND: 153_s0, 153_s1, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: sub_en, cin, b_sel |
| 3 | **AND** | `12` | `34` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | `10` | `00010000` | GND: sub_en, cin, 153_s1, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s0 |
| 4 | **OR** | `12` | `34` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | `36` | `00110110` | GND: sub_en, cin, 153_s0, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s1 |
| 5 | **XOR** | `12` | `34` | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | `26` | `00100110` | GND: sub_en, cin, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s0, 153_s1 |
| 6 | **NOT** | `12` | `00` | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | `ED` | `11101101` | GND: sub_en, cin, b_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s0, 153_s1, c3_sel |
| 7 | **PASS_A** | `12` | `FF` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | `12` | `00010010` | GND: sub_en, cin, 153_s1, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s0 |
| 8 | **PASS_B** | `FF` | `34` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | `34` | `00110100` | GND: sub_en, cin, 153_s1, b_sel, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: 153_s0 |
| 9 | **INC** | `12` | `00` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | `13` | `00010011` | GND: sub_en, cin, 153_s0, 153_s1, b_sel, c3_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: b_const_sel |
| 10 | **DEC** | `12` | `00` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | `11` | `00010001` | GND: sub_en, cin, 153_s0, 153_s1, b_sel, c3_sel; VCC: b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7 |
| 11 | **CMP** | `12` | `34` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | `DE` | `11011110` | GND: 153_s0, 153_s1, c3_sel, b_const_sel, b_const_bit1, b_const_bit2, b_const_bit3, b_const_bit4, b_const_bit5, b_const_bit6, b_const_bit7; VCC: sub_en, cin, b_sel |

Columns: **b_cst** = `net_b_const_sel`, **b_hi** = `net_b_const_bit1..7` (same value), **Y LEDs** = MSB left (y7) … LSB (y0).

## Smoke vectors (B3a first)

| Op | A | B | Expected Y |
|----|---|---|------------|
| SUB | 0x12 | 0x34 | 0xDE |
| XOR | 0x12 | 0x34 | 0x26 |
| INC | 0x12 | — | 0x13 |

See phased bring-up: [hw-bringup-b3.md](hw-bringup-b3.md).
