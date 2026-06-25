# Archived — hardware MMU v1.1 (not adopted)

**Active normative:** v1.0 flat 64 KiB — [memory-map.md](../../hardware/memory-map.md) · [system-architecture.md](../../hardware/system-architecture.md)

Discrete **71024** page-table MMU, `/NMI` fault glue, and demand-paging software track were **planned but not adopted** for the breadboard.

## Rationale

1. **No process isolation needed** — single-threaded Forth interpreter; no preemptive multitasking or GUI; virtual address spaces add no value.
2. **Historical alignment** — Apple II and Commodore 64 use **64 KB flat** memory (RAM / ROM / I/O regions only; no MMU).
3. **Lower hardware complexity** — removing PTE SRAM, address MUX, and fault glue reduces breadboard wire hops and improves bus integrity.

## Contents

| File | Role |
|------|------|
| [discrete-mmu-spec-v1.1.md](discrete-mmu-spec-v1.1.md) | 71024 PTE SRAM + glue |
| [memory-map-v1.1.md](memory-map-v1.1.md) | Extended map with MMU window |
| [fault-logic-v1.1.md](fault-logic-v1.1.md) | Page fault / NMI |
| [os-paging-v1.1.md](os-paging-v1.1.md) | Software paging model |
| [M2c-mmu-v1.1.md](M2c-mmu-v1.1.md) | Bring-up milestone (archived) |
| [BOM-v1.1-delta.md](BOM-v1.1-delta.md) | Extra parts if MMU were built |

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | Moved to archive; v1.0 flat map remains normative |
