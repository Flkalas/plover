# OS paging curriculum v1.1

**Related:** [discrete-mmu-spec-v1.1.md](../hardware/discrete-mmu-spec-v1.1.md) · [fault-logic-v1.1.md](../hardware/fault-logic-v1.1.md) · [microcode-spec.md](../hardware/microcode-spec.md) §10 · [software-roadmap.md](software-roadmap.md)

Software milestone **S8** (planned) — demand paging and protection on **v1.1 hardware MMU**.

---

## 1. Prerequisites

| Layer | Gate |
|-------|------|
| Hardware | [M2c-mmu-v1.1.md](../hw-bringup/M2c-mmu-v1.1.md) sign-off |
| Kernel | S6 microkernel boot under identity PTE |
| VM | `decode_addr_v1_1` / `plover_mmu::mmu_v1_1` tests PASS |

---

## 2. Learning goals

- **Demand paging:** valid bit clear → `/NMI` → handler loads frame from 71024 swap bank (`A16=1`).
- **Protection:** write to `WE=0` page → segfault-class `/NMI`.
- **Replacement:** LRU or FIFO on 16 virtual pages (4 KiB) — swap to upper 64 KiB of 71024, not vFDD (teaching shortcut).

---

## 3. NMI handler contract

| Step | Action |
|------|--------|
| 1 | Vector @ **`$FFFA`** — save GPRs on kernel stack (software) |
| 2 | Read faulting `VA` from agreed MMIO scratch or fixed register (TBD in kernel port) |
| 3 | If `!V`: allocate frame — copy from swap or zero-fill; set PTE |
| 4 | If `!WE` ∧ write: terminate task or COW lab (advanced) |
| 5 | `RET` or `JMP` to resumed `PC` |

---

## 4. PTE management API (kernel)

```text
pte_load_identity()     — 16 entries PA=i, V=1, WE=1
pte_map(va_page, pa_page, we)
pte_unmap(va_page)      — V=0
swap_in(va_page, slot)  — 71024 A16=1 kernel copy
swap_out(va_page, slot)
```

---

## 5. VM / test plan

| Test | Description |
|------|-------------|
| `test_mmu_fault_nmi.py` | Hardware fault truth |
| `test_os_page_fault.py` | (future) handler installs PTE |
| `test_os_swap_lru.py` | (future) 17th page evicts LRU |

---

## 6. Relation to vFDD

Mailbox vFDD remains bulk storage ([virtual-fdd.md](../copro/virtual-fdd.md)). v1.1 **71024 swap** is silicon-fast lab backing; optional extension copies swap slots to vFDD for persistence.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-13 | **v1.1** — curriculum outline (S8) |
