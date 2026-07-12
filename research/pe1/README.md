# PE1 — pipelined FE1 extension

**Build code:** **PE1** (research, non-normative)  
**Gate:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md)  
**Prior FE1 No (shared bus):** [primitive-one-clock](../primitive-one-clock/SUMMARY-REPORT.md)

## Goal

Recover owner intent (**~1 macro retired per SYS** in steady state) by **adding parts** and a **simple IF|EX pipeline** — Isetta-like simplicity (**no branch prediction**), Gigatron-like throughput shape for **native** Plover macros.

**Not:** one shared A-bus edge that fetch+executes a whole multi-byte insn alone (still impossible).

## Questions

1. With Harvard-like program/data split + pipe latches, can ALU streams approach **IPC ≈ 1.0**?
2. What BOM delta vs Gi1 is required?
3. How do mem ops, multi-byte immediates, and taken branches appear as **visible bubbles** (not hidden idle phases)?

## Deliverables

| File | Role |
|------|------|
| [architecture.md](architecture.md) | IF/EX, bubbles, ports |
| [bom-delta.md](bom-delta.md) | Extra DIP desk list |
| [isetta-gigatron-map.md](isetta-gigatron-map.md) | Peer mapping |
| [opcode-pipe-table.md](opcode-pipe-table.md) | Per-op SYS / stalls |
| [model/](model/) | `pe1_ipc_model.py` + pytest |
| [SUMMARY-REPORT.md](SUMMARY-REPORT.md) | Verdict |

## Contrast

| Study | Approach |
|-------|----------|
| [primitive-one-clock](../primitive-one-clock/) FE1 | Same-tick F+E on one bus → **No** |
| FE2 | Delete idle; serial F then E |
| [cpld-ustep](../cpld-ustep/) | Hide control on fast CU clock |
| **PE1** | Overlap IF of N+1 with EX of N; pay for ports |

## Out of scope

- Normative Gi1 / whitepaper edits (except no — research only; one SUMMARY pointer from primitive-one-clock)
- Branch prediction / speculative execution
- Flash `$4000` CW return
- Breadboard build this pass

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial PE1 desk study |
