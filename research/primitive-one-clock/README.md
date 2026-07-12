# Primitive one-clock — regression feasibility

**Status:** Research (non-normative)  
**Normative baseline:** Gi1 multiphase FSM — [microcode-spec.md](../../reference/hardware/microcode-spec.md) · [M3b-fetch-execute.md](../../reference/hw-bringup/M3b-fetch-execute.md)  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md)

## Goal (owner intent)

Restore a **programmer-transparent** timing model:

- Instruction cost is a **small visible integer of SYS clocks**, not a hidden CU phase schedule with idle slots.
- **FE1:** one instruction’s fetch+execute in **1 SYS** (literal “1 work = 1 clock”).
- **FE2:** if FE1 fails on shared bus — fixed **fetch 1 + execute 1** (no idle phases).

This study **reverses** the [`cpld-ustep`](../cpld-ustep/) pedagogy priority (keep multiphase e-IPC). Here the priority is **delete hidden cost**, not hide it on USTEP.

## Questions

1. Can FE1 work on the current von Neumann breadboard at 2 MHz for the core ISA?
2. If not, is FE2 a viable **primitive regression** that restores programmer control?
3. What are the hard blockers (bus, multi-byte fetch, CALL/RET stack)?

## Deliverables

| File | Role |
|------|------|
| [programmer-model.md](programmer-model.md) | Visible SYS cost vs Gi1 hidden phases |
| [opcode-fe-table.md](opcode-fe-table.md) | **FE2 per-opcode F/E sheet (draft)** |
| [architecture.md](architecture.md) | FE1 / FE2 CU sketch on existing BOM |
| [bus-timing-feasibility.md](bus-timing-feasibility.md) | Per-opcode desk fit |
| [model/](model/) | `cycle_model.py` + pytest |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Verdicts |

## Out of scope

- Normative edits to `reference/**` or whitepaper
- Breadboard reburn / CPLD `.pld` implementation
- PLL / second oscillator
- Archive tarball restore

## Related

| Build | Role |
|-------|------|
| [PE1](../pe1/) | IF\|EX + ports for FE1-class throughput |
| [P12](../p12/) | PE1 + FE2 stretch / no-idle / FE2 fallback |

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Link P12 |
| 2026-07-13 | Initial desk study |
