# Plover documentation

Design notes and **hwsim** for Plover — **v1.0 breadboard CPU** (CPLD GPR ~40 MC + 138×2 CE + 10b CW).

## Active (v1.0)

| Document | Description |
|----------|-------------|
| [system-architecture.md](system-architecture.md) | **Single source of truth** (v1.0) |
| [hardware-architecture-synthesis.md](hardware-architecture-synthesis.md) | Decisions, parasitics, breadboard vs PCB |
| [memory-map.md](memory-map.md) | Address map · 138×2 + gate decode |
| [rom-architecture.md](rom-architecture.md) | Control / Boot / Utility ROM |
| [cpld-system-controller.md](cpld-system-controller.md) | ATF1504 GPR-only (~40 MC) |
| [microcode-spec.md](microcode-spec.md) | 10b CW · Reg_Sel in Flash |
| [mailbox-protocol.md](mailbox-protocol.md) | MMIO `$FF00` |
| [rp2350-coprocessor.md](rp2350-coprocessor.md) | Copro board |
| [display-console.md](display-console.md) | **40×25** · 320×240@30 → HDMI 640×480@60 |
| [bootloader.md](bootloader.md) | Boot · Run handoff |
| [boot-jmp-handoff.md](boot-jmp-handoff.md) | **JMP chain load** (no DIP/RESET) |
| [implementation-plan-v0.1.md](implementation-plan-v0.1.md) | Milestones |
| **[hw-bringup/](hw-bringup/README.md)** | **M1–M5 breadboard** — [breadboard-wiring](hw-bringup/breadboard-wiring.md) |
| [plans/](plans/) | Active bring-up plans (B3) |
| [alu-opcodes-timing.md](alu-opcodes-timing.md) | ALU comb delay |
| [hw-sim.md](hw-sim.md) | `python -m hwsim` · `plover_vm` |
| [hw-bringup-alu8-assembly-spec.md](hw-bringup-alu8-assembly-spec.md) | M1 — ALU8 조립 |
| [reviewer-handoff.md](reviewer-handoff.md) | 검토자 인수인계 |
| [roadmap-next.md](roadmap-next.md) | Roadmap |
| [fpga-target-guide.md](fpga-target-guide.md) | FPGA / Verilog 타깃 |

## Archive

| Path | Contents |
|------|----------|
| [archive/pre-v1.0/](archive/pre-v1.0/README.md) | v0.2 all-in-CPLD snapshots |
| [archive/pre-v0.1/](archive/pre-v0.1/README.md) | v0.1 external-GPR bring-up |

## Project root

- [../README.md](../README.md)
- [../BOM.md](../BOM.md) · [../BOM-3v3.md](../BOM-3v3.md) · [bom-maintenance.md](bom-maintenance.md)
