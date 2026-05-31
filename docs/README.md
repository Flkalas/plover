# Plover documentation

Design notes and **hwsim** for Plover — **v0.1 CPU** (574×4 GPR + ATF1504AS system CPLD).

## Active (v0.1)

| Document | Description |
|----------|-------------|
| [system-architecture.md](system-architecture.md) | **Single source of truth** |
| [memory-map.md](memory-map.md) | Address map · Mode A/B |
| [rom-architecture.md](rom-architecture.md) | Control / Boot / Utility ROM |
| [cpld-system-controller.md](cpld-system-controller.md) | ATF1504AS decode · GPR load |
| [microcode-spec.md](microcode-spec.md) | 8b CW · ISA |
| [mailbox-protocol.md](mailbox-protocol.md) | MMIO `$FF00` |
| [rp2350-coprocessor.md](rp2350-coprocessor.md) | Copro board |
| [bootloader.md](bootloader.md) | Boot · Run handoff |
| [implementation-plan-v0.1.md](implementation-plan-v0.1.md) | Milestones |
| [alu-opcodes-timing.md](alu-opcodes-timing.md) | ALU comb delay |
| [hw-sim.md](hw-sim.md) | `python -m hwsim` · `plover_vm` |
| [reviewer-handoff.md](reviewer-handoff.md) | **검토자 인수인계** |
| [roadmap-next.md](roadmap-next.md) | Roadmap |

## Archive

Pre-v0.1 specs (v0.2 / v1.x): [archive/pre-v0.1/](archive/pre-v0.1/README.md)

| Old active path | v0.1 replacement |
|-----------------|------------------|
| `*-v2.0.md` | unversioned name above |
| `microcode-spec-v1.*.md` | [microcode-spec.md](microcode-spec.md) |
| `v*.x-implementation-plan.md` | [implementation-plan-v0.1.md](implementation-plan-v0.1.md) |

## Project root

- [../README.md](../README.md)
- [../BOM.md](../BOM.md)
