# Plover hardware simulation (`hw/`)

Electrical netlist, timing, and block tests for breadboard bring-up.

| Path | Description |
|------|-------------|
| [netlist/blocks/](netlist/blocks/) | YAML block netlists (clock, ALU, register) |
| [timing/](timing/) | Datasheet delays (74HC, memory) |
| [models/](models/) | Chip behavior metadata |
| [tests/](tests/) | Stimulus + timing checks |
| [viewer/](viewer/index.html) | Static waveform / report viewer |
| [kicad/](kicad/plover/) | KiCad schematics (see [docs/hw-schematic.md](../docs/hw-schematic.md)) |

Run simulator: [docs/hw-sim.md](../docs/hw-sim.md)

```bash
python -m hwsim run --all
```
