# regfile — v0.2 GPR (4×574 + 8×153)

| Item | Value |
|------|-------|
| GPR | `U_REG_R0` … `U_REG_R3` — 74HC574, `D*` ← `net_y*`, `Q*` → `net_r{n}_q*` |
| A MUX | `U_MUX_A_0..3` — 153, select `net_src_reg0..1` |
| B MUX | `U_MUX_B_0..3` — 153, select `net_dst_reg0..1` |
| CP | `U_CP_DEC` (138) + per-reg `~Y` AND `net_cmp_n` AND `net_clk2` |
| IMM dst | `bus_en=11` → `net_bus_imm` → 157 overrides `dst_reg` → R2 CP |

**Outputs to ALU:** `net_a0..7`, `net_b0..7`  
**Inputs from ALU:** `net_y0..7` (write data)

Generate: `python tools/gen_regfile_netlist.py`
