# KiCad ↔ YAML netlist naming

hwsim uses YAML netlists as the machine-readable source of truth. KiCad schematics in [`hw/kicad/plover/`](../hw/kicad/plover/) should export netlists that match these rules.

## Reference designators

Format: `{BLOCK}_{PART}_{IDX}`

| Block | Example |
|-------|---------|
| Clock | `U_CLK_74`, `U_CLK_OSC` |
| ALU | `U_ALU_283_LO`, `U_ALU_283_HI` |
| Register | `U_REG_574_0` |
| PC | `U_PC_161_0` … `U_PC_161_3` |

## Net names

Format: `net_{domain}_{name}` or bus `net_{name}[msb:lsb]`

Examples:

- `net_osc` — 4 MHz oscillator output
- `net_clk2` — 2 MHz divided clock
- `net_data_bus` — 8-bit data (width in net entry)

## Power pins

Mark in YAML as `VCC: pwr_vcc`, `GND: pwr_gnd`. Diff and sim ignore `type: power` nets.

## KiCad export

```bash
kicad-cli sch export netlist hw/kicad/plover/plover.kicad_sch -o hw/kicad/export/plover.net
python -m hwsim diff-kicad hw/kicad/export/plover.net hw/netlist/blocks/clock.yaml
```

CI compares normalized `(ref, pin) → net` pairs from KiCad S-expression netlist vs YAML.

## Hierarchy

One YAML file per block sheet. Top-level CPU integration uses `include` (future) — MVP validates blocks independently.
