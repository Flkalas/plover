# Memory Map v1.1 — MMU extension

**Related:** [memory-map.md](memory-map.md) (v1.0 normative CPU map) · [discrete-mmu-spec-v1.1.md](discrete-mmu-spec-v1.1.md)

v1.1 **does not change** the CPU-visible 16-bit map table in [memory-map.md](memory-map.md) §1—3. It adds **translation and backing** below the decode layer.

---

## 1. CPU virtual map (unchanged)

Same as v1.0:

| Range | Boot | Run |
|-------|------|-----|
| `$0000—$07FF` | Boot ROM | RAM |
| `$0800—$FEFF` | RAM | RAM |
| `$FF00—$FFFB` | Mailbox | Mailbox |
| `$FFFC—$FFFF` | ROM vector | RAM vector |

**MMU bypass:** Mailbox, ROM fetch, and reset `$FFFC` mux — addresses go to v1.0 decode **without** PTE lookup.

---

## 2. Main physical RAM — 2× IS62C256 (unchanged)

| Chip | CPU range (after MMU) |
|------|------------------------|
| **RAM_1** | `PA15=0` → `$0000—$7FFF` |
| **RAM_2** | `PA15=1` ∧ ¬Mailbox | `$8000—$FFFF` (except `$FF00—$FFFB`) |

**Translation:** CPU `VA` → PTE → `PA[15:0]` → then v1.0 A15 bank rules apply to `PA`.

Example: `VA=$4000` with `PTE[4]={PA=4,V=1,WE=1}` → `PA=$4000` → RAM_1.

---

## 3. MMU physical — 71024S15TYG (128 KiB)

Not on the CPU 16-bit address bus. Accessed only via:

- **Combinatorial read:** `VA[15:12]` during every translated RAM cycle (`A16=0`).
- **Kernel programmed I/O:** glue-decoded window or dedicated `/WE` cycle to load PTE bytes and swap pages (`A16=0` table, `A16=1` swap).

| 71024 `A16` | Size | Purpose |
|-------------|------|---------|
| 0 | 64 KiB | PTE table (16×6 bit used minimum) + metadata headroom |
| 1 | 64 KiB | Hardware swap frames |

---

## 4. MAP_MODE

Unchanged — operator DIP. MMU identity map required for Boot ROM `JMP $0800` handoff ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)).

---

## 5. Decode stack (v1.1)

```text
VA ──► [Mailbox/ROM bypass?] ──no──► 71024 PTE ──► PA ──► 138×2 + glue ──► /CE
         │ yes
         └──► v1.0 decode (no PTE)
```

---

## Change log

| Date | Note |
|------|------|
| 2026-06-13 | **v1.1** — MMU layer documented; v1.0 map by-reference |
