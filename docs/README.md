# Plover documentation

Design notes and **hwsim** electrical simulation for the Plover 8-bit VLIW-RISC breadboard CPU.

## Index

| Document | Description |
|----------|-------------|
| [hw-sim.md](hw-sim.md) | **Electrical timing sim** — `python -m hwsim`, netlist YAML, block tests |
| [hw-schematic.md](hw-schematic.md) | KiCad ↔ YAML netlist naming |
| [roadmap-next.md](roadmap-next.md) | Next steps — hwsim expansion, breadboard bring-up |
| [hw-bringup-b3.md](hw-bringup-b3.md) | **B3** ALU + 574 breadboard procedure |
| [archive/README.md](archive/README.md) | Archived Gemini logs and Cursor plans |
| [archive/gemini/](archive/gemini/) | Original design conversation exports |
| [archive/plans/](archive/plans/) | Completed Verilog simulator plan |

Archived Verilog / ISA docs: [../archive/verilog-sim/docs/microcode-spec.md](../archive/verilog-sim/docs/microcode-spec.md)

## Project root

- [../README.md](../README.md) — project overview, hwsim quick start
- [../BOM.md](../BOM.md) — bill of materials
- [../archive/README.md](../archive/README.md) — archived Verilog stack

## Code map (active)

| Path | README |
|------|--------|
| `hwsim/` | [../hwsim/README.md](../hwsim/README.md) |
| `hw/` | [../hw/README.md](../hw/README.md) |

## Code map (archived)

| Path | README |
|------|--------|
| `archive/verilog-sim/rtl/` | [../archive/verilog-sim/rtl/README.md](../archive/verilog-sim/rtl/README.md) |
| `archive/verilog-sim/sim/` | [../archive/verilog-sim/sim/README.md](../archive/verilog-sim/sim/README.md) |
| `archive/verilog-sim/web/` | [../archive/verilog-sim/web/README.md](../archive/verilog-sim/web/README.md) |
