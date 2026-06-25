# Plover — external documentation (normative)

**Audience:** learners, external reviewers, breadboard builders.

This tree contains **v1.0 confirmed facts** only — hardware specs, bring-up, software stack, boot, and copro MMIO protocols. No internal simulators, CI commands, or research exploration history.

## Start here

| Document | Description |
|----------|-------------|
| [project/plover-whitepaper.md](project/plover-whitepaper.md) | Project overview |
| [hardware/system-architecture.md](hardware/system-architecture.md) | **Single source of truth** (v1.0) |
| [hw-bringup/README.md](hw-bringup/README.md) | M1–M5 breadboard bring-up |

## Hardware (v1.0)

| Document | Description |
|----------|-------------|
| [hardware/microcode-spec.md](hardware/microcode-spec.md) | FSM-only ISA, idx5 |
| [hardware/cpld-system-controller.md](hardware/cpld-system-controller.md) | ATF1504 GPR + idx5 FSM |
| [hardware/memory-map.md](hardware/memory-map.md) | Address map |
| [hardware/rom-architecture.md](hardware/rom-architecture.md) | Boot / utility ROM |
| [hardware/alu-opcodes-timing.md](hardware/alu-opcodes-timing.md) | ALU comb delay |
| [hardware/hw-schematic.md](hardware/hw-schematic.md) | Netlist / KiCad rules |
| [hardware/alu8-phase-b.md](hardware/alu8-phase-b.md) | ALU phase-B integration |
| [hardware/fpga-target-guide.md](hardware/fpga-target-guide.md) | FPGA target (future) |

## Software, boot, copro

- [software/software-roadmap.md](software/software-roadmap.md) — S0–S7 milestones
- [boot/](boot/) — boot chain
- [copro/](copro/) — RP2350 mailbox, VDU, vFDD, HID, APU

## Other tiers

| Tier | Path |
|------|------|
| Developer (sim, VM, CI) | [../developer/README.md](../developer/README.md) |
| Research | [developer research index](developer research index) |
| Archive | [../archive/README.md](../archive/README.md) |
