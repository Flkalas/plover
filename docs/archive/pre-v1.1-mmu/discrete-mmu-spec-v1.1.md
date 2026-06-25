# Discrete MMU Specification v1.1

**Status:** Archived ??hardware MMU v1.1 **not adopted**.  
**Active normative:** v1.0 flat 64 KiB ??[memory-map.md](../../hardware/memory-map.md) Â· [system-architecture.md](../../hardware/system-architecture.md)  
**Rationale:** [README.md](README.md)

**Related (archived):** [memory-map-v1.1.md](memory-map-v1.1.md) Â· [fault-logic-v1.1.md](fault-logic-v1.1.md)

v1.1 adds an **external MMU** built from **71024S15TYG** (128 KiB async SRAM) plus discrete 74HC glue. v1.0 **IS62C256Ã—2** remains **main execution RAM** (64 KiB). v1.0 CE decode (138Ã—2 + glue) and **ATF1504 GPR** are unchanged.

---

## 1. Block diagram

```text
  CPU VA[15:0]
       ??       ?œâ? VA[15:12] ?€?€??71024 (A16=0 PTE read) ?€?€??PA[15:12], V, WE
       ??                     ??       ??                     ?”â??€??Fault logic ?€?€??/NMI
       ??       ?œâ? VA[11:0] ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??IS62 A[11:0]
       ?”â? PA[15:12] from PTE ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??IS62 A[15:12]

  71024 A16=1 (kernel only) ?€?€ swap bank (64 KiB)
```

Reference: [`decode_addr_v1_1()`](../../hw/logic/mmu_v1_1.py) Â· [`MmuV11`](../../crates/plover_mmu/src/mmu_v1_1.rs).

---

## 2. Parts

| Part | Role |
|------|------|
| **71024S15TYG** | MMU SRAM ??PTE table + hardware swap store (**not** main RAM) |
| **2Ã— IS62C256AL** | Main physical RAM (64 KiB) ??same as v1.0 |
| **74HC08/32/04** (+ 157/245 as needed) | Fault detect, 71024 `/OE`/`/WE`, A16 swap select |

---

## 3. Page size and PTE

- **Page size:** 4 KiB (`VA[11:0]` = offset, passed through to main RAM).
- **Virtual pages:** 16 (`VA[15:12]` indexes PTE table).
- **PTE width:** 6 bits (stored in 71024 byte; upper bits reserved).

| PTE bit | Field | Meaning |
|---------|-------|---------|
| [3:0] | `PA[15:12]` | Physical page on IS62 main map |
| [4] | **V** | Valid ??`0` ??fault |
| [5] | **WE** | Write enable ??`0` + CPU write ??fault |

**PTE address (71024, `A16=0`):** index = `VA[15:12]`, byte offset = `{index, 4'b0}` in lower 64 KiB of 71024 (only 16 entries used at bring-up).

---

## 4. 71024 internal 128 KiB map

| `A16` | Region | Access |
|-------|--------|--------|
| **0** | Lower 64 KiB | PTE / MMU metadata (kernel write, MMU comb read on every translated RAM access) |
| **1** | Upper 64 KiB | **Hardware swap** ??demand-paging backing; **kernel-only** via A16 glue |

Swap replaces disk I/O for teaching LRU/FIFO page replacement ([os-paging-v1.1.md](os-paging-v1.1.md)).

---

## 5. Address translation (RAM only)

MMU applies to **main RAM** CPU accesses only. **No translation** for:

- Mailbox `$FF00??FFFB`
- Boot ROM overlay / `$FFFC` vector (v1.0 [memory-map.md](memory-map.md) decode)
- Instruction fetch from SST39 when `ROM_CS` active

**Algorithm:**

1. `va` = CPU virtual address (16-bit).
2. If v1.0 decode ??ROM or Mailbox: **bypass MMU** (use `va` for decode; no PTE read).
3. Else: read `pte = PTE[va[15:12]]` from 71024 (`A16=0`).
4. If `!V` or (`!WE` ??write): assert **`/NMI`** (see [fault-logic-v1.1.md](fault-logic-v1.1.md)).
5. `phys = (pte.pa_hi << 12) | (va & 0xFFF)`.
6. Drive IS62 with `phys[15:0]`; `RAM1`/`RAM2` select via `phys[15]` and v1.0 glue.

**Identity map (boot):** kernel pre-init sets `PTE[i] = { PA=i, V=1, WE=1 }` for all 16 entries before enabling user tasks.

---

## 6. PTE programming (kernel)

- Kernel writes 71024 with **`A16=0`**, dedicated `/WE` gated so MMU lookup (read) and PTE store (write) are **mutually exclusive** with IS62 main fetch on the shared data bus.
- Glue owns: `MMU_LUT_OE`, `MMU_LUT_WE`, `MAIN_OE`, `MAIN_WE` interlock ([fault-logic-v1.1.md](fault-logic-v1.1.md) Â§3).

---

## 7. Timing budget

| Stage | Budget | Part |
|-------|--------|------|
| PTE read | **15 ns** | 71024S15TYG |
| Main access | **45 ns** | IS62C256AL-45 |
| Fault comb | **??5 ns** | 74HC |
| **Serial total** | **~65 ns** | Within 2 MHz (500 ns) cycle |

10 MHz stretch requires `hwsim` / measured closure ([`test_mmu_timing_v1_1.py`](../../tests/test_mmu_timing_v1_1.py)).

---

## 8. Simulator API

| Layer | Symbol |
|-------|--------|
| Python | `hw.logic.mmu_v1_1.PteEntry`, `decode_addr_v1_1`, `Mmu71024State` |
| Rust | `plover_mmu::mmu_v1_1::{PteEntry, MmuV11, translate}` |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-13 | **v1.1** ??71024 discrete MMU; IS62 main unchanged |
