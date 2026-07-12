# P12 — PE1 + FE2 discipline

**Build code:** **P12** (research, non-normative)  
**Meaning:** PE1 pipe machine + FE2 stretch / no-idle / fallback rules  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md)  
**Parents:** [pe1](../pe1/SUMMARY-REPORT.md) · [primitive-one-clock](../primitive-one-clock/SUMMARY-REPORT.md) FE2

## Goal

Keep PE1’s **IF|EX overlap** and Harvard-like ports, and absorb FE2’s **honest** rules:

- No Gi1 multiphase **idle** in EX
- Lab fail → **stretch** (visible SYS), not hope / hidden CU padding
- PROG/DATA isolation fail → **serial FE2 fallback** (not wishful FE1)

## Questions

1. Does optimistic P12 match PE1 IPC (ALU stream → 1.0)?
2. What does one FE2-style stretch pass do to MEM / BEQ / CALL / RET?
3. How costly is `fallback_fe2` vs pipe P12?
4. Does BOM change vs PE1? (**No** — FE2 rules add 0 DIP.)

## Deliverables

| File | Role |
|------|------|
| [architecture.md](architecture.md) | PE1 pipe + FE2 EX rules + fallback |
| [programmer-model.md](programmer-model.md) | Visible N SYS; stretch language |
| [opcode-pipe-table.md](opcode-pipe-table.md) | Pipe costs + stretch column |
| [fallback-fe2.md](fallback-fe2.md) | When/how to degrade to serial FE2 |
| [bom-delta.md](bom-delta.md) | Same as PE1 (link) |
| [timing-budget.md](timing-budget.md) | Link PE1; stretch = more SYS |
| [mailbox-2mhz.md](mailbox-2mhz.md) | Link PE1; stretch MEM if RP late |
| [clock-candidates.md](clock-candidates.md) | Link PE1; stretch before raise f_SYS |
| [beq-lab.md](beq-lab.md) | Link PE1; prefer stretch over clock hope |
| [model/](model/) | `p12_ipc_model.py`, mailbox + pytest |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Verdict |

## Contrast

| Study | Approach |
|-------|----------|
| FE2 | Serial F then E; delete idle |
| PE1 | Overlap IF/EX; pay for ports |
| **P12** | PE1 + stretch sheet + FE2 fallback |
| cpld-ustep | Hide control on fast CU clock |

## Out of scope

- Normative Gi1 / whitepaper edits
- Branch prediction
- Breadboard build this pass

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial P12 desk study |
