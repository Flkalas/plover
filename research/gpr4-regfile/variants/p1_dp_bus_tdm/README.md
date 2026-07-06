# p1_dp_bus_tdm — CPLD-DP WinCUPL skeleton

**Parent:** [../../p1-bus-tdm/README.md](../../p1-bus-tdm/README.md)  
**Pin map:** [../../p1-bus-tdm/pin-map.md](../../p1-bus-tdm/pin-map.md)

P1 datapath: 4-GPR, single `q_bus`, internal `u_phase` @ 4 MHz, `alu_a_le` pulse, GPR FF @ `clk_sys` (÷2).

**Topology default:** C0 — `clk_4m` on pin 43; `clk_sys` synthesized inside.

**Not for production burn** until timing mitigation (M1/M2) chosen.

## Files

| File | Role |
|------|------|
| [system_ctrl.pld](system_ctrl.pld) | DP equations |

## Local fit

```text
wincupl system_ctrl.pld system_ctrl.tt system_ctrl.jed
```

Desk expectation: **28/32 pins PASS**; MC ~48–58 (desk).
