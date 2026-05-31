# Plover documentation

Design notes and **hwsim** electrical simulation for the Plover 8-bit VLIW-RISC breadboard CPU.

## Index

| Document | Description |
|----------|-------------|
| [hw-sim.md](hw-sim.md) | **Electrical timing sim** — `python -m hwsim`, netlist YAML, block tests |
| [hw-schematic.md](hw-schematic.md) | KiCad ↔ YAML netlist naming |
| [roadmap-next.md](roadmap-next.md) | Next steps — hwsim expansion, breadboard bring-up |
| [hw-bringup-b3.md](hw-bringup-b3.md) | **B3a/b/c** ALU + 574 phased breadboard guide |
| [hw-bringup-b3-opcode.md](hw-bringup-b3-opcode.md) | Opcode → control DIP cheat sheet (12 rows) |
| [microcode-spec-v0.2.md](microcode-spec-v0.2.md) | **VLIW CW v0.2 (frozen)** — 4-GPR, 2-addr, bus_en+ctrl |
| [v0.2-implementation-plan.md](v0.2-implementation-plan.md) | **v0.2 구현 단계·의존 관계** — Flash CW → full CPU |
| [hw-bringup-p1-datapath.md](hw-bringup-p1-datapath.md) | Phase1 datapath hwsim (V1+V2 stub CW) |
| [archive/README.md](archive/README.md) | Archived Gemini logs and Cursor plans |
| [archive/gemini/](archive/gemini/) | Original design conversation exports |
| [archive/plans/](archive/plans/) | Completed Verilog simulator plan |

Archived Verilog / ISA docs: [../archive/verilog-sim/docs/microcode-spec.md](../archive/verilog-sim/docs/microcode-spec.md) (v0.1) · Active hardware CW: [microcode-spec-v0.2.md](microcode-spec-v0.2.md)

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
