# Plover reference specifications

**Audience:** learners, external reviewers, breadboard builders.

v1.0 confirmed facts — hardware specs, bring-up, software stack, boot, copro MMIO. No simulators, CI commands, or research history.

## Start here

| Document | Description |
|----------|-------------|
| [plover-whitepaper.md](../plover-whitepaper.md) | Project overview (repository root) |
| [hardware/system-architecture.md](hardware/system-architecture.md) | **Single source of truth** (v1.0) |
| [hardware/control-and-decode.md](hardware/control-and-decode.md) | CPLD vs Flash vs ALU decode |
| [hw-bringup/README.md](hw-bringup/README.md) | M1–M5 breadboard bring-up |

## Hardware (v1.0)

| Document | Description |
|----------|-------------|
| [hardware/microcode-spec.md](hardware/microcode-spec.md) | FSM-only ISA, idx5 |
| [hardware/cpld-system-controller.md](hardware/cpld-system-controller.md) | ATF1504 GPR + idx5 FSM |
| [hardware/memory-map.md](hardware/memory-map.md) | Address map |
| [hardware/alu-opcodes-timing.md](hardware/alu-opcodes-timing.md) | ALU comb delay |
| [fixtures/README.md](fixtures/README.md) | Frozen burn images |

## Software, boot, copro

- [software/software-roadmap.md](software/software-roadmap.md) — S0–S7 milestones
- [boot/](boot/) — boot chain
- [copro/](copro/) — RP2350 mailbox, VDU, vFDD

Archived code, research, and developer notes: [archive/MANIFEST.md](../archive/MANIFEST.md).
