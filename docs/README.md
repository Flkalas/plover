# Plover documentation

Design notes and simulators for Plover — **v1.0 breadboard CPU** (CPLD GPR ~40 MC + 138×2 CE + 10b CW).

## Quick start

- Project overview: [../README.md](../README.md)
- Electrical sim: `python -m hwsim run --all` — [simulation/hw-sim.md](simulation/hw-sim.md)
- Logic VM: `cargo run -p plover_vm` — [simulation/vm-rust.md](simulation/vm-rust.md)
- BOM: [../BOM.md](../BOM.md) · packages [project/parts-on-hand.md](project/parts-on-hand.md) · maintenance [project/bom-maintenance.md](project/bom-maintenance.md)

---

## Hardware (v1.0 normative)

| Document | Description |
|----------|-------------|
| [hardware/system-architecture.md](hardware/system-architecture.md) | **Single source of truth** (v1.0) |
| [hardware/hardware-architecture-synthesis.md](hardware/hardware-architecture-synthesis.md) | Decisions, parasitics, breadboard vs PCB |
| [hardware/memory-map.md](hardware/memory-map.md) | Address map · 138×2 + gate decode |
| [hardware/rom-architecture.md](hardware/rom-architecture.md) | Control / Boot / Utility ROM |
| [hardware/cpld-system-controller.md](hardware/cpld-system-controller.md) | ATF1504 GPR-only (~40 MC) |
| [hardware/microcode-spec.md](hardware/microcode-spec.md) | 10b CW · Reg_Sel in Flash |
| [hardware/alu-opcodes-timing.md](hardware/alu-opcodes-timing.md) | ALU comb delay |
| [hardware/alu8-phase-b.md](hardware/alu8-phase-b.md) | ALU Phase B2 implementation notes |
| [hardware/hw-schematic.md](hardware/hw-schematic.md) | KiCad ↔ YAML netlist naming |
| [hardware/fpga-target-guide.md](hardware/fpga-target-guide.md) | FPGA / Verilog target (planning) |

---

## Bring-up (M1–M5)

| Document | Description |
|----------|-------------|
| [hw-bringup/README.md](hw-bringup/README.md) | **Canonical** milestone index |
| [hw-bringup/breadboard-wiring.md](hw-bringup/breadboard-wiring.md) | 138×2, gates, CW latch |
| [hw-bringup/alu8-assembly-spec.md](hw-bringup/alu8-assembly-spec.md) | M1 — ALU8 조립 |
| [hw-bringup/b3-opcode.md](hw-bringup/b3-opcode.md) | Opcode DIP cheat sheet (generated) |

---

## Simulation

| Document | Description |
|----------|-------------|
| [simulation/hw-sim.md](simulation/hw-sim.md) | `python -m hwsim` · netlist timing |
| [simulation/cyclesim.md](simulation/cyclesim.md) | Micro-phase structural sim |
| [simulation/vm-rust.md](simulation/vm-rust.md) | Rust `plover_vm` CLI |
| [simulation/reviewer-handoff.md](simulation/reviewer-handoff.md) | 검토자 인수인계 |

---

## Software & runtime

| Document | Description |
|----------|-------------|
| [software/software-roadmap.md](software/software-roadmap.md) | S0–S7 milestones |
| [software/software-memory-layout.md](software/software-memory-layout.md) | RAM / kernel / load regions |
| [software/plover-asm.md](software/plover-asm.md) | Assembler (S1) |
| [software/calling-convention-v0.1.md](software/calling-convention-v0.1.md) | CALL/RET (S2) |
| [software/forth-system.md](software/forth-system.md) | Forth core (S3) |
| [software/forth-os-services.md](software/forth-os-services.md) | Forth OS (S4) |
| [software/subset-c.md](software/subset-c.md) | Subset C compiler (S5) |
| [software/os-kernel.md](software/os-kernel.md) | C microkernel (S6) |
| [copro/virtual-fdd.md](copro/virtual-fdd.md) | vFDD (S7a) |
| [software/plover-fat.md](software/plover-fat.md) | PLFS (S7b) |
| [software/program-loader.md](software/program-loader.md) | `.PLR` loader (S7c) |
| [software/dos-shell.md](software/dos-shell.md) | PL-DOS shell (S7d) |
| [software/basic-system.md](software/basic-system.md) | Tiny BASIC + game |
| [software/game-api.md](software/game-api.md) | Game builtins |
| [software/runtime-api.md](software/runtime-api.md) | Runtime syscalls |
| [software/demo-program-spec.md](software/demo-program-spec.md) | Demo / diagnostic spec |
| [software/plover-linker.md](software/plover-linker.md) | PLX linker format |

---

## Coprocessor & I/O

| Document | Description |
|----------|-------------|
| [copro/rp2350-coprocessor.md](copro/rp2350-coprocessor.md) | Copro board |
| [copro/mailbox-protocol.md](copro/mailbox-protocol.md) | MMIO `$FF00` |
| [copro/display-console.md](copro/display-console.md) | 40×25 · 320×240@30 → HDMI |
| [copro/audio-apu.md](copro/audio-apu.md) | APU |
| [copro/input-hid.md](copro/input-hid.md) | Keyboard / mouse |
| [copro/device-discovery.md](copro/device-discovery.md) | Slot device scan |
| [copro/serial-module.md](copro/serial-module.md) | UART slot peripheral |
| [copro/virtual-fdd.md](copro/virtual-fdd.md) | Virtual floppy |

---

## Boot

| Document | Description |
|----------|-------------|
| [boot/bootloader.md](boot/bootloader.md) | Boot · Run handoff |
| [boot/boot-jmp-handoff.md](boot/boot-jmp-handoff.md) | JMP chain load |
| [boot/baremetal-gpio-smoke.md](boot/baremetal-gpio-smoke.md) | ROM Stage1 GPIO smoke |

---

## Project & procurement

| Document | Description |
|----------|-------------|
| [project/implementation-plan-v0.1.md](project/implementation-plan-v0.1.md) | Milestones M1–M5 |
| [project/roadmap-next.md](project/roadmap-next.md) | Roadmap |
| [project/parts-on-hand.md](project/parts-on-hand.md) | **Purchased packages** (v1.0 breadboard) |
| [project/bom-maintenance.md](project/bom-maintenance.md) | BOM history & checks |
| [project/purchase-devicesmart.md](project/purchase-devicesmart.md) | DeviceSmart order log |
| [project/purchase-2026-06-01-followup.md](project/purchase-2026-06-01-followup.md) | 2026-06-01 follow-up |
| [plans/](plans/README.md) | Active bring-up plans |

---

## Archive

| Path | Contents |
|------|----------|
| [archive/pre-v1.0/](archive/pre-v1.0/README.md) | v0.2 all-in-CPLD snapshots |
| [archive/pre-v0.1/](archive/pre-v0.1/README.md) | v0.1 external-GPR bring-up |
| [archive/bringup-legacy/](archive/bringup-legacy/README.md) | Superseded root bring-up copies |
| [archive/sessions/](archive/sessions/README.md) | Completed session handoffs |
| [archive/gemini/](archive/gemini/) | Design conversation exports |
| [archive/plans/](archive/plans/README.md) | Completed Cursor plans |
