# M2c ??71024 MMU bring-up (v1.1)

**Status:** Archived ??hardware MMU v1.1 **not adopted**.  
**Rationale:** [README.md](README.md)

| Field | Value |
|-------|-------|
| **마일?�톤** | M2c (MMU) ??**not on v1.0 bring-up path** |
| **?�행** | [M2b](../../hw-bringup/M2b-memory.md) sign-off ??IS62×2, MAP_MODE, `mem_decode` PASS |
| **Spec (archived)** | [discrete-mmu-spec-v1.1.md](discrete-mmu-spec-v1.1.md) · [fault-logic-v1.1.md](fault-logic-v1.1.md) |

**71024S15TYG = MMU only.** IS62C256×2 remains main RAM ([BOM-v1.1-delta.md](BOM-v1.1-delta.md)).

---

## 1. Parts added

| Part | Role |
|------|------|
| 71024S15TYG | PTE table (`A16=0`) + swap bank (`A16=1`) |
| 74HC08/32/04 | Fault ??`/NMI`; `/OE`/`/WE` interlock |

---

## 2. 71024 smoke (MMU chip alone)

1. `A16=0`, address `0x0000` (PTE slot 0), write `0x3F` (V+WE+PA=0xF) via manual `/WE`.
2. Read back ??`/OE` pulse.
3. Repeat for address `0x0010` (PTE slot 1).

**Pass:** data matches written PTE bytes.

---

## 3. PTE lookup path

1. Load identity PTEs: slot `i` @ address `i<<4` ??`{PA=i, V=1, WE=1}` (6 bits in low byte).
2. CPU (or manual) presents `VA=$0800` ??observe glue driving 71024 with `VA[15:12]=0`.
3. `PA[15:12]` from PTE ??IS62 `A15:12`; `VA[11:0]` ??IS62 `A11:0`.
4. Write `0x5A` to `$0800`, read back.

**Pass:** byte stored in IS62 at `$0800`.

---

## 4. Remap test

1. Set PTE[4] ??`{PA=7, V=1, WE=1}`.
2. Access `$4000` ??physical IS62 `$7000`.
3. Write/read distinct pattern at `$4000`.

**Pass:** pattern visible at IS62 `$7000`, not `$4000`.

---

## 5. Fault / `/NMI`

1. Clear PTE[2].V ??access `$2000`.
2. **Pass:** `/NMI` asserts (logic probe); IS62 `/CE` does not glitch spuriously.
3. Set PTE[3].WE=0; write to `$3000`.
4. **Pass:** `/NMI` on write attempt.

Install NMI handler @ `$FFFA` (Run map) before automated tests.

Sim gate:

```bash
pytest tests/test_mem_decode_v1_1.py tests/test_mmu_fault_nmi.py tests/test_mmu_timing_v1_1.py -q
```

---

## 6. A16 swap bank (kernel)

1. Assert kernel `A16=1` glue (manual strap for bring-up).
2. Read/write swap frame in 71024 upper 64 KiB.
3. **Pass:** no contention with PTE read (`A16=0`) when glue interlocks `/OE`.

---

## 7. Boot / Run

1. **Boot map:** ROM `$0000` ??MMU bypass (no PTE fetch).
2. Load identity PTE table before user code.
3. **JMP $0800** ??RAM band unchanged ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)).

---

## 8. M2c sign-off

- [ ] 71024 PTE read/write smoke
- [ ] Identity map + `$0800` R/W via IS62
- [ ] Page remap `$4000` ??`$7000`
- [ ] Invalid PTE ??`/NMI`
- [ ] RO write ??`/NMI`
- [ ] pytest MMU suite PASS
- [ ] v1.0 `test_mem_decode_breadboard.py` still PASS

---

## 9. Next

??M3a control store (unchanged) or OS paging lab ([os-paging-v1.1.md](os-paging-v1.1.md))
