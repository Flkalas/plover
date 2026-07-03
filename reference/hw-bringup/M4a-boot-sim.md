# M4a — Boot chain (historical simulation gate)

| Field | Value |
|-------|-------|
| **Milestone** | M4a |
| **Goal** | JMP handoff: boot ROM → RAM `$0800` → **`JMP $0800`** |
| **Status** | Logic verified 2026-06-08 (archived VM — see [archived-code-guide.md](../../archive/MANIFEST.md)) |
| **Normative** | [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) |

---

## 1. What was proven

Before breadboard (M4b), the boot chain was checked with archived logic VM:

1. Boot ROM copies kernel sector to RAM `$0800`
2. SP/RP/GPR pre-init cells written
3. **`JMP $0800`** reaches kernel stub

**Pass criterion for M4b:** reproduce the same byte images on real Flash/SRAM ([fixtures](../fixtures/README.md)).

---

## 2. Frozen images (active repo)

| Image | Document |
|-------|----------|
| Boot ROM `$0000` | [boot-rom.md](../fixtures/boot-rom.md) |
| Reset vector `$FFFC` | [boot-vector.md](../fixtures/boot-vector.md) |
| Kernel smoke `$0800` | [add_imm-sram.md](../fixtures/add_imm-sram.md) (or kernel stub in boot-rom tail) |

v1.0 breadboard: **no Flash `$4000` CW** — CPLD FSM only ([M3a](M3a-control-store.md)).

---

## 3. M4a sign-off (historical)

- [x] JMP handoff chain verified (archived VM, 2026-06)
- [ ] M4b hardware burn matches frozen fixtures

---

## 4. Next

→ [M4b-boot-hardware.md](M4b-boot-hardware.md)
