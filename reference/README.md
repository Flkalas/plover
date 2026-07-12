# Plover reference specifications

**Audience:** learners, external reviewers, breadboard builders.

**v1.0 P12** confirmed facts — hardware specs, bring-up, software stack, boot, copro MMIO. No simulators, CI commands, or research history.

## Start here

| Document | Description |
|----------|-------------|
| [plover-whitepaper.md](../plover-whitepaper.md) | **Root** — project overview, ISA §6, pipe narrative |
| [hardware/system-architecture.md](hardware/system-architecture.md) | v1.0 P12 architecture |
| [hardware/cpld-pipe-cu.md](hardware/cpld-pipe-cu.md) | **Active pipe CU** |
| [hardware/control-and-decode.md](hardware/control-and-decode.md) | CPLD vs Flash vs ALU decode |
| [hw-bringup/README.md](hw-bringup/README.md) | M1–M5 breadboard bring-up (partially legacy Gi1) |

### Truth cascade (edit order)

| Tier | Path | Role |
|------|------|------|
| **Root** | [plover-whitepaper.md](../plover-whitepaper.md) §6 | ISA / pipe narrative |
| **Reference** | `reference/**` (this tree) | Normative detail; **CU = cpld-pipe-cu** |
| **Machine** | `simulators/cyclesim/` | **Legacy Gi1 multiphase golden** until pipe rewrite |
| **CPLD** | pipe CU `.pld` | **Design fits pending**; Gi1 PLD = legacy |

ISA or pipe CU changes: **whitepaper first** → reference → machine code → CPLD regen.

**Archived:** Gi1 idx5 — [archive/gi1-v1.0-normative/](../archive/gi1-v1.0-normative/).

## Hardware (v1.0 P12)

| Document | Description |
|----------|-------------|
| [hardware/cpld-pipe-cu.md](hardware/cpld-pipe-cu.md) | **Pipe CU** — states, bubbles, stretch, timing |
| [hardware/microcode-spec.md](hardware/microcode-spec.md) | ISA + pipe SYS sheet |
| [hardware/cpld-system-controller.md](hardware/cpld-system-controller.md) | Dual CPLD CU/DP ports |
| [hardware/memory-map.md](hardware/memory-map.md) | Address map |
| [hardware/alu-opcodes-timing.md](hardware/alu-opcodes-timing.md) | ALU comb delay |
| [hardware/ttl-computer-comparison.md](hardware/ttl-computer-comparison.md) | Plover vs other TTL homebrew CPUs |
| [hardware/cu-dp-comparison.md](hardware/cu-dp-comparison.md) | CU·DP vs peers |
| [hardware/rom-comparison.md](hardware/rom-comparison.md) | ROM/Flash count and roles |
| [hardware/clock-comparison.md](hardware/clock-comparison.md) | Clock / throughput comparison |
| [fixtures/README.md](fixtures/README.md) | Frozen burn images |

## Software, boot, copro

- [software/software-roadmap.md](software/software-roadmap.md) — S0–S7 milestones
- [boot/](boot/) — boot chain
- [copro/](copro/) — RP2350 mailbox, VDU, vFDD

Archived code, research, and developer notes: [archive/MANIFEST.md](../archive/MANIFEST.md).
