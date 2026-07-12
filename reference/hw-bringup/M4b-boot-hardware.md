# M4b — Boot ROM hardware smoke (상세)

| Field | Value |
|-------|-------|
| **Milestone** | M4b |
| **Goal** | 빵판에서 product boot: RESET → READ → `JMP $0800` |
| **선행** | [M3b](M3b-fetch-execute.md), [M4a](M4a-boot-sim.md) |
| **Normative** | [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) · [fixtures](../fixtures/README.md) |

---

## 1. NOR 이미지 (동결)

Burn boot and vector fixtures to SST39. Flash physical map: [rom-architecture.md](../hardware/rom-architecture.md).

| Region | Frozen source |
|--------|---------------|
| Boot `$0000+` | [boot-rom.md](../fixtures/boot-rom.md) |
| Vector `$FFFC` | [boot-vector.md](../fixtures/boot-vector.md) |
| RAM smoke `$0800` | [add_imm-sram.md](../fixtures/add_imm-sram.md) (teaching) |

프로그래머로 byte-per-line 이미지를 SST39에 Program + Verify.

**Readback spot checks:**

| Address | Expect |
|---------|--------|
| `$0000` | first boot byte from fixture |
| `$FFFC` | `00 00` (vector → `$0000`) |
| handoff near `$0600` | `05 00 08` (`JMP $0800`) |

---

## 2. G1 — NOR 소각

1. SST39 소켓, 5 V.
2. Program merged image from §1 fixtures.
3. Verify + readback.

---

## 3. G2 — RESET boot entry

1. `MAP_MODE=0` (Boot DIP).
2. `RESET` → fetch from ROM `$0000` region.

---

## 4. G3 — vFDD sector 0 READ (optional)

RP2350 Mailbox — sector 0 kernel image → RAM `$0800`. See [mailbox-protocol.md](../copro/mailbox-protocol.md).

**Teaching path:** pre-load [add_imm-sram.md](../fixtures/add_imm-sram.md) at `$0800`, test JMP only.

---

## 5. G4 — JMP `$0800` + pre-init

See [boot-jmp-handoff.md](../boot/boot-jmp-handoff.md) §5.1 — SP `$0E00`, RP `$0F00`, PC → `$0800`.

---

## 6. G5 — Recovery (manual)

Boot image ends **HALT** path: DIP Run → RESET → fetch from RAM vector.

---

## 7. M4b sign-off

- [ ] G1 readback
- [ ] G2 RESET fetch
- [ ] G3 or teaching path documented
- [ ] G4 pre-init + JMP
- [ ] Lab log: NOR rev, git SHA

---

## 8. Next

→ [M5-cpu-e2e.md](M5-cpu-e2e.md)
