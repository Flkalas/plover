# KiCad — Plover hardware schematics

Human-editable schematics for breadboard wiring. Machine verification uses YAML netlists in [`hw/netlist/blocks/`](../../netlist/blocks/).

## Layout (planned hierarchy)

| Sheet | YAML block |
|-------|----------------|
| `sheet_clock.kicad_sch` | `clock.yaml` |
| `sheet_alu.kicad_sch` | `alu283.yaml` |
| `sheet_reg.kicad_sch` | `reg574.yaml` |

## Export for diff

```bash
kicad-cli sch export netlist sheet_clock.kicad_sch -o export/clock.net
python -m hwsim diff-kicad hw/kicad/export/clock.net hw/netlist/blocks/clock.yaml
```

A sample netlist matching `clock.yaml` is in [`export/clock.net`](export/clock.net) for CI.

## Naming

See [docs/hw-schematic.md](../../../docs/hw-schematic.md).
