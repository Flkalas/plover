# Plover hardware simulation (`hw/`)

Electrical netlist, timing, and block tests for breadboard bring-up.

| Path | Description |
|------|-------------|
| [netlist/blocks/](netlist/blocks/) | YAML block netlists (clock, **alu8**, **alu_b3**, **alu_b3_clock**, alu283, register) |
| [timing/](timing/) | Datasheet delays (74HC, memory) |
| [models/](models/) | Chip behavior metadata |
| [tests/](tests/) | Stimulus + timing checks |
| [viewer/](viewer/index.html) | Static waveform / report viewer |
| [kicad/](kicad/plover/) | KiCad schematics (see [docs/hw-schematic.md](../docs/hw-schematic.md)) |

See [netlist/blocks/alu8.md](netlist/blocks/alu8.md) for full 8-bit ALU BOM wiring and `alu_sel` map.  
Breadboard phases: [docs/hw-bringup-b3.md](../docs/hw-bringup-b3.md) · [docs/hw-bringup-b3-opcode.md](../docs/hw-bringup-b3-opcode.md).

```bash
python -m hwsim run --all
```
