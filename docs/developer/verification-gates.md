# Developer verification gates

**Breadboard bring-up only.** The active repo has no sim CI — frozen tables live in normative docs.

## Electrical / timing (lab)

| Check | Normative reference |
|-------|---------------------|
| 2 MHz clock at CPLD | [M2a-cpld-decode.md](../normative/hw-bringup/M2a-cpld-decode.md) |
| ALU opcode timing budget | [alu-opcodes-timing.md](../normative/hardware/alu-opcodes-timing.md) §3.1 |
| b3 manual DIP vectors | [b3-opcode.md](../normative/hw-bringup/b3-opcode.md) |

Use an oscilloscope for setup/hold and `t_pd` slack — not restored sim bundles.

## Milestone sign-off (hardware)

| Milestone | Checklist doc |
|-----------|---------------|
| M1 ALU | [M1-alu.md](../normative/hw-bringup/M1-alu.md) · [M1-b3-procedure.md](../normative/hw-bringup/M1-b3-procedure.md) |
| M2a CPLD decode | [M2a-cpld-decode.md](../normative/hw-bringup/M2a-cpld-decode.md) |
| M2b GPR / memory | [M2b-gpr-datapath.md](../normative/hw-bringup/M2b-gpr-datapath.md) |
| M3a FSM table | [M3a-control-store.md](../normative/hw-bringup/M3a-control-store.md) §2 |
| M3b fetch/execute | [M3b-fetch-execute.md](../normative/hw-bringup/M3b-fetch-execute.md) |
| M4 boot | [M4b-boot-hardware.md](../normative/hw-bringup/M4b-boot-hardware.md) · [fixtures](../normative/fixtures/README.md) |
| M5 integration | [M5-cpu-e2e.md](../normative/hw-bringup/M5-cpu-e2e.md) |

## Archived automation

Historical pytest / hwsim / VM gates: [archived-code-guide.md](archived-code-guide.md).
