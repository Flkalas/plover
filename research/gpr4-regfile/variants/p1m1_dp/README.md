# p1m1_dp — CPLD-DP WinCUPL skeleton

**Parent:** [../../p1m1-dual574/README.md](../../p1m1-dual574/README.md)  
**Pin map:** [../../p1m1-dual574/pin-map.md](../../p1m1-dual574/pin-map.md)

P1M1 datapath: P1 `q_bus` TDM + **574 ALU B** latch + `op_fetch` half-cycle gate.

**Fork of:** [../p1_dp_bus_tdm/system_ctrl.pld](../p1_dp_bus_tdm/system_ctrl.pld)

| Δ vs P1 | Detail |
|---------|--------|
| `PIN 33` | `alu_b_le` — one-shot @ T2 end (250 ns) |
| `op_fetch` | Toggle FF @ `clk_sys`; gates `q_bus` and LE pulses |
| `q_bus` | No direct ALU B wire — 574B Q → `net_b*` |

**Topology default:** C0 — `clk_4m` pin 43; internal ÷2 → `clk_sys`.

**Not for production burn** until WinCUPL fit + scope gates V1–V4 ([timing-closed.md](../../p1m1-dual574/timing-closed.md) §6).

## Files

| File | Role |
|------|------|
| [system_ctrl.pld](system_ctrl.pld) | DP equations |

## Local fit

```text
wincupl system_ctrl.pld system_ctrl.tt system_ctrl.jed
```

Desk expectation: **29/32 pins PASS**; MC ~50–60 (desk).
