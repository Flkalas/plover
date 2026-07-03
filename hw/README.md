# Plover hardware simulation (`hw/`)

Electrical netlist, timing, and block tests for breadboard bring-up.

| Path | Description |
|------|-------------|
| [netlist/blocks/](netlist/blocks/) | YAML block netlists (clock, **alu8**, **alu_b3**, **alu_b3_clock**, alu283, register) |
| [timing/](timing/) | Datasheet delays (74HC, memory) |
| [models/](models/) | Chip behavior metadata |
| [pinout/](pinout/) | **DIP pin maps** (BOM 74HC — for breadboard / diagrams) |
| [tests/](tests/) | Stimulus + timing checks |
| [viewer/](viewer/index.html) | Static waveform / report viewer |
| [viewer/schematic.html](viewer/schematic.html) | DIP schematic SVG viewer (zoom) |
| [kicad/](kicad/plover/) | KiCad schematics (see [docs/normative/hardware/hw-schematic.md](../docs/normative/hardware/hw-schematic.md)) |

See [netlist/blocks/alu8.md](netlist/blocks/alu8.md) for **Phase B2** ALU (14 IC: `U_ALU_153_0..7`, `157_YBP`; CMP via SUB; SUB **151 ns**, logic **46 ns** @ max).  
Breadboard phases: [docs/normative/hw-bringup/M1-b3-procedure.md](../docs/normative/hw-bringup/M1-b3-procedure.md) · [docs/normative/hw-bringup/b3-opcode.md](../docs/normative/hw-bringup/b3-opcode.md).

Boot ROM: **`boot_rom.hex`** = JMP product path; **`boot_rom_manual.hex`** = DIP Run recovery — [docs/normative/boot/boot-jmp-handoff.md](../docs/normative/boot/boot-jmp-handoff.md).

Regenerate after ALU edits ([docs/developer/simulation/hw-sim.md](../docs/developer/simulation/hw-sim.md#alu-netlist-regeneration-phase-a)):

```bash
python tools/gen_alu_decode_netlist.py
python tools/gen_alu8_netlist.py
python tools/gen_alu_b3_netlist.py
python tools/gen_alu_b3_clock_netlist.py
python -m hwsim run --all
```
