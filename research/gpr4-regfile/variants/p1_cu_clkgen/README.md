# p1_cu_clkgen — CPLD-CU clock divider skeleton (C1)

**Parent:** [../../p1-bus-tdm/clock-topologies.md](../../p1-bus-tdm/clock-topologies.md)  
**Use with:** OSC 4 MHz on CU pin 43; DP still receives OSC tap @ 4 MHz (C0/C1 hybrid).

## Files

| File | Role |
|------|------|
| [system_ctrl.pld](system_ctrl.pld) | ÷2 → `clk_2m_out`, ÷4 → `clk_1m_out` |

**Note:** Full CU idx5 FSM is **not** included — clockgen overlay only for fit spike.

## Pin warning

Adding 2 clock exports to rev G CU (26/32) → **28/32** if no other changes.  
Extended G-IC `r_sel` (+4 wires) on CU → **31/32** — see [pin-map.md](../../p1-bus-tdm/pin-map.md).
