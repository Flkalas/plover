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
| [plans/](plans/) | Active bring-up plans (B3) |
| [alu-opcodes-timing.md](alu-opcodes-timing.md) | ALU comb delay |
| [hw-sim.md](hw-sim.md) | `python -m hwsim` · `plover_vm` |
| [reviewer-handoff.md](reviewer-handoff.md) | **검토자 인수인계** |
| [roadmap-next.md](roadmap-next.md) | Roadmap |
| [fpga-target-guide.md](fpga-target-guide.md) | **FPGA / Verilog** 타깃·교육 보드·외부 ROM/RAM (기준 문서) |

## FPGA track (planning)

| Document | Description |
|----------|-------------|
| [fpga-target-guide.md](fpga-target-guide.md) | Resource models A/B/C, EP4CE6, speed, future `hw/rtl/v0.1/` |

TTL/PCB 실기와 **병렬** — [implementation-plan-v0.1.md](implementation-plan-v0.1.md) §2 참고.

## Software (VM)

| Document | Description |
|----------|-------------|
| [software-roadmap.md](software-roadmap.md) | **S0–S7 milestone index** |
| [software-memory-layout.md](software-memory-layout.md) | RAM regions · Forth · PL-DOS |
| [plover-asm.md](plover-asm.md) | Normative assembler (S1) |
| [calling-convention-v0.1.md](calling-convention-v0.1.md) | CALL/RET · stacks (S2) |
| [forth-system.md](forth-system.md) | Forth kernel (S3) |
| [forth-os-services.md](forth-os-services.md) | Block I/O · console (S4) |
| [subset-c.md](subset-c.md) | Subset C compiler (S5) |
| [os-kernel.md](os-kernel.md) | C microkernel (S6) |
| [pl-dos-roadmap.md](pl-dos-roadmap.md) | PL-DOS master (S7) |
| [virtual-fdd.md](virtual-fdd.md) | vFDD driver (S7a) |
| [plover-fat.md](plover-fat.md) | PLFS on-disk (S7b) |
| [program-loader.md](program-loader.md) | `.PLR` format (S7c) |
| [dos-shell.md](dos-shell.md) | PL-DOS shell (S7d) |

## Archive

Pre-v0.1 specs (v0.2 / v1.x): [archive/pre-v0.1/](archive/pre-v0.1/README.md)

| Old active path | v0.1 replacement |
|-----------------|------------------|
| `*-v2.0.md` | unversioned name above |
| `microcode-spec-v1.*.md` | [microcode-spec.md](microcode-spec.md) |
| `v*.x-implementation-plan.md` | [implementation-plan-v0.1.md](implementation-plan-v0.1.md) |
| `.cursor/plans/` (historical) | [archive/plans/](archive/plans/README.md) |

## Project root

- [../README.md](../README.md)
- [../BOM.md](../BOM.md) (5 V 빵판) · [../BOM-3v3.md](../BOM-3v3.md) (3.3 V PCB)
