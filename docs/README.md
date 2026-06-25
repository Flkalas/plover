# Plover documentation

Design notes and simulators for Plover — **v1.0 breadboard CPU** (FSM-only, idx5, CPLD ~38 MC).

### Version labels

| Label | Meaning | Examples |
|-------|---------|----------|
| **v1.0** | Normative **breadboard hardware** — always current pre-release | [system-architecture.md](hardware/system-architecture.md), [BOM.md](../BOM.md) |
| **software v0.1** | **S0–S7 / copro protocol / VM** feature track | [software-roadmap.md](software/software-roadmap.md) |
| **prototype-flash-cw** | Superseded 10b Flash CW prototype | [archive/prototype-flash-cw/](archive/prototype-flash-cw/README.md) |
| **research / archive** | Exploration, MMU drafts, superseded prototypes | [hardware/research/](hardware/research/README.md) |

Hardware prose uses **v1.0**; software and copro API scope stays **software v0.1** unless noted.

## Tiers

| Tier | Audience | Start here |
|------|----------|------------|
| **Normative** | Learners, bring-up | [hardware/system-architecture.md](hardware/system-architecture.md) · [plover-whitepaper.md](project/plover-whitepaper.md) |
| **Research** | Design history | [hardware/research/README.md](hardware/research/README.md) |
| **Developer** | Sim, VM, CI | [simulation/hw-sim.md](simulation/hw-sim.md) · `pytest` |

## Quick start (developers)

- Project overview: [../README.md](../README.md)
- Electrical sim: `python -m hwsim run --all` — [simulation/hw-sim.md](simulation/hw-sim.md)
- Logic VM: `cargo run -p plover_vm` — [simulation/vm-rust.md](simulation/vm-rust.md)
- BOM: [../BOM.md](../BOM.md)

---

## Hardware (v1.0 normative)

| Document | Description |
|----------|-------------|
| [hardware/system-architecture.md](hardware/system-architecture.md) | **Single source of truth** (v1.0) |
| [hardware/microcode-spec.md](hardware/microcode-spec.md) | FSM-only ISA, idx5 |
| [hardware/cpld-system-controller.md](hardware/cpld-system-controller.md) | ATF1504 GPR + idx5 FSM (~38 MC) |
| [hardware/memory-map.md](hardware/memory-map.md) | Address map · 138×2 + gate decode |
| [hardware/rom-architecture.md](hardware/rom-architecture.md) | Boot / utility ROM (`$4000` unused) |
| [hardware/alu-opcodes-timing.md](hardware/alu-opcodes-timing.md) | ALU comb delay |

## Research

| Document | Description |
|----------|-------------|
| [hardware/research/README.md](hardware/research/README.md) | Research index |
| [hardware/research/design-rationale-v1.0.md](hardware/research/design-rationale-v1.0.md) | Why v1.0 |
| [hardware/cpu-4axis-arch-search-report.md](hardware/cpu-4axis-arch-search-report.md) | 4-axis search record |

## Bring-up (M1–M5)

| Document | Description |
|----------|-------------|
| [hw-bringup/README.md](hw-bringup/README.md) | Milestone index |
| [hw-bringup/breadboard-wiring.md](hw-bringup/breadboard-wiring.md) | SoC wiring |

## Simulation (developer)

| Document | Description |
|----------|-------------|
| [simulation/hw-sim.md](simulation/hw-sim.md) | `python -m hwsim` |
| [simulation/vm-rust.md](simulation/vm-rust.md) | Rust `plover_vm` |

## Software & runtime

| Document | Description |
|----------|-------------|
| [software/software-roadmap.md](software/software-roadmap.md) | S0–S7 milestones |
| [project/plover-whitepaper.md](project/plover-whitepaper.md) | Overview whitepaper |
