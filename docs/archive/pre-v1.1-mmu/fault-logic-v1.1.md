# Fault Logic v1.1 — MMU protection and /NMI

**Related:** [discrete-mmu-spec-v1.1.md](discrete-mmu-spec-v1.1.md) · [microcode-spec.md](microcode-spec.md) §10 · [memory-map-v1.1.md](memory-map-v1.1.md)

v1.1 adds **combinatorial fault detection** outside the CPLD. Faults drive **`/NMI`** (active low) into the CPU sequencer.

---

## 1. Fault conditions

Let `pte_v` = PTE Valid bit, `pte_we` = PTE write-enable, `cpu_wr` = latched CW `MEM_WR` during execute phase.

```text
FAULT = !pte_v  OR  (!pte_we AND cpu_wr)
```

| Condition | OS meaning |
|-----------|------------|
| `!V` | Invalid page — segfault / demand page not present |
| `!WE` ∧ write | Write to read-only page |

Fault logic is **74HC** (08/32/04); **not** inside ATF1504.

---

## 2. /NMI wiring

| Signal | Direction | Note |
|--------|-----------|------|
| **`/NMI`** | Fault → CPU | Active **low**; async to clock; sampled by sequencer |
| **`NMI_ACK`** | (optional future) | Not in v1.1 baseline |

**Masking:** NMI is **not** maskable via CW (unlike planned maskable IRQ). v1.0 had no IRQ; v1.1 adds NMI only for MMU faults.

---

## 3. Bus arbitration glue

Prevent LUT (71024) vs main (IS62) data-bus contention:

| Mode | `MMU_LUT_OE` | `MMU_LUT_WE` | `MAIN_OE` | `MAIN_WE` |
|------|--------------|--------------|-----------|-----------|
| Normal RAM read | 1 (PTE comb read) | 0 | 1 | 0 |
| Normal RAM write | 1 | 0 | 0 | 1 |
| Kernel PTE write | 0 | 1 | 0 | 0 |
| Kernel swap (A16=1) | 0 | per R/W | 0 | 0 |

`/OE`/`/WE` setup documented in [M2c-mmu-v1.1.md](../hw-bringup/M2c-mmu-v1.1.md).

---

## 4. NMI vector and handler entry

On **`/NMI` assert** (falling edge while CPU running):

1. Sequencer completes current micro-phase boundary (or aborts MEM phase — see microcode §10).
2. **`PC ← $FFFA`** (word-aligned NMI vector in RAM under Run map, or ROM under Boot — operator must place handler).
3. **`/NMI` deasserts** when PTE fault condition clears (combinatorial — handler must fix PTE or halt).

Normative micro-sequence: [microcode-spec.md](microcode-spec.md) §10.

---

## 5. hwsim / VM

Python: `decode_addr_v1_1(...).nmi`  
Rust: `translate(...).fault_nmi`  
Tests: [`test_mmu_fault_nmi.py`](../../tests/test_mmu_fault_nmi.py)

---

## Change log

| Date | Note |
|------|------|
| 2026-06-13 | **v1.1** — discrete fault → /NMI |
