# KiCad ↔ YAML netlist naming

pre-flight sim uses YAML netlists as the machine-readable source of truth. KiCad schematics in [`hw/kicad/plover/`](../hw/kicad/plover/) should export netlists that match these rules.

**DIP pin numbers** (breadboard): [`hw/pinout/`](../hw/pinout/) — one YAML per BOM part; developer verification gate.  
Logical pins in netlists (`A0`, `1Y`, …) map to physical pins via `plover_netlist` sections where names differ (e.g. 74HC283 `S0` → DIP pin 4).

## Reference designators

Format: `{BLOCK}_{PART}_{IDX}`

| Block | Example |
|-------|---------|
| Clock | `U_CLK_74`, `U_CLK_OSC` |
| ALU | `U_ALU_283_LO/HI`, `U_ALU_153_0`…`7`, `U_ALU_157_YBP_*`, `U_ALU_CMP_SUB` (behavioral) |
| Register | `U_REG_574_0`, `U_REG_574_ACC` (B3 accumulator) |
| PC | `U_PC_161_0` … `U_PC_161_3` |

## Net names

Format: `net_{domain}_{name}` or bus `net_{name}[msb:lsb]`

Examples:

- `net_osc` / `CLK_SYS` — **2.000 MHz** oscillator
- `net_clk2` — buffered system clock (= `CLK_SYS`)
- `net_a0` … `net_a7`, `net_b0` … `net_b7` — ALU operands
- `net_y0` … `net_y7` — ALU result
- `net_cin`, `net_153_s0`, `net_153_s1`, `net_bctrl0`…`3`, `net_lgc0`…`3` — ALU control (VLIW or test)
- `net_cmp_z`, `net_cmp_c_ge` — CMP flags from SUB (`net_y`, `net_c_hi`; no 7485)
- `net_d0` … `net_d7` — 574 D inputs (B3: tied to `net_y*`)
- `net_q0` … `net_q7` — 574 Q outputs

## Power pins

Mark in YAML as `VCC: pwr_vcc`, `GND: pwr_gnd`. Diff and sim ignore `type: power` nets.

## KiCad export

```bash
kicad-cli sch export netlist hw/kicad/plover/plover.kicad_sch -o hw/kicad/export/plover.net
```

CI compares normalized `(ref, pin) → net` pairs from KiCad S-expression netlist vs YAML.

## Hierarchy

One YAML file per block sheet. Top-level CPU integration uses `include` (future) — MVP validates blocks independently.
