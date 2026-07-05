# Plover reference specifications

**Audience:** learners, external reviewers, breadboard builders.

v1.0 confirmed facts — hardware specs, bring-up, software stack, boot, copro MMIO. No simulators, CI commands, or research history.

## Start here

| Document | Description |
|----------|-------------|
| [plover-whitepaper.md](../plover-whitepaper.md) | **Root** — project overview, ISA §6, FSM narrative |
| [hardware/system-architecture.md](hardware/system-architecture.md) | v1.0 architecture (cascade from whitepaper) |
| [hardware/control-and-decode.md](hardware/control-and-decode.md) | CPLD vs Flash vs ALU decode; truth cascade §6 |
| [hw-bringup/README.md](hw-bringup/README.md) | M1–M5 breadboard bring-up |

### Truth cascade (edit order)

| Tier | Path | Role |
|------|------|------|
| **Root** | [plover-whitepaper.md](../plover-whitepaper.md) §6 | ISA / FSM narrative |
| **Reference** | `reference/**` (this tree) | Normative detail, bring-up, frozen fixtures |
| **Machine** | `simulators/cyclesim/data/isa.py`, `fsm_table.py` | Executable golden |
| **CPLD** | `cpld_fsm/hdl/` — `gen_ctrl_lut.py`, `system_ctrl.pld` | Bitstream source |

ISA or idx5 changes: **whitepaper first** → reference → machine code → CPLD regen → pytest.

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
