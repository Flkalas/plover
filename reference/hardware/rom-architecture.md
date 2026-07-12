# ROM Architecture v1.0

**Related:** [system-architecture.md](system-architecture.md) · [memory-map.md](memory-map.md) · [microcode-spec.md](microcode-spec.md) · [rom-comparison.md](rom-comparison.md) (peer ROM roles)

ROM is the **code of law** for the system: deterministic rules for boot, datapath control, and fixed assets.

---

## 1. Three segments (logical)

| Segment | Purpose | CPU visibility |
|---------|---------|----------------|
| **Control** | **CPLD FSM** (idx5) — no Flash CW @ `$4000` | Execute phases in ATF1504 |
| **Boot** | POST, bootloader, reset vector | Mode A: `$0000–$07FF`, `$FFFC` |
| **Utility** | Fonts, LUTs, fixed routines | ROM in Mode A; shadowed to RAM `$0800+` |

---

## 2. Physical device

**Single** `SST39SF010A-70-4C-PHE` — 128K×8 parallel NOR, **PDIP-32** ([parts-on-hand.md](../project/parts-on-hand.md)).

| Property | Rationale |
|----------|-----------|
| Parallel | Power-on execute — no SPI init |
| Single 8-bit data bus | Matches TTL datapath |
| 128 KB | Boot + CW + fonts + headroom |

### Flash physical layout

| Flash offset | Content | CPU map (Mode A) |
|--------------|---------|------------------|
| `$0000–$07FF` | Boot + bootloader | `$0000–$07FF` ROM |
| `$0800–$3FFF` | Utility (fonts, tables) | Copy source |
| `$4000–$4FFF` | **Reserved** (no CW burn; FSM-only) | Not used in normative v1.0 |
| `$FFFC–$FFFF` | Reset vector image | `$FFFC` enclave |

Normative v1.0: Flash **`$4000–$4FFF` is unused** — control is entirely in the CPLD FSM ([microcode-spec.md](microcode-spec.md)). The superseded 10b CW layout is documented in [prototype-flash-cw](../archive/prototype-flash-cw/README.md).

---

## 3. Control (CPLD FSM — normative v1.0)

Micro-phase strobes come from the **ATF1504 phase FSM** keyed by `(opcode[4:0]<<2)|phase` — see [cpld-system-controller.md](cpld-system-controller.md).

Verify opcode table: [M3a-control-store.md](../hw-bringup/M3a-control-store.md) §2.

Archive prototype Flash CW: [prototype-flash-cw](../archive/prototype-flash-cw/README.md) (not v1.0 breadboard).

### Archived Flash CW (prototype-flash-cw only)

```
store_index = ((opcode[3:0] << 2) | phase[1:0])   // idx4, 64 slots
Flash_lo    = $4000 + 2 * store_index
```

| Property | Value (prototype-flash-cw) |
|----------|-------|
| Logical index width | 6 bits (`opcode[3:0]` × `phase[1:0]`) |
| Active slots (macro ISA) | 16 opcode nibbles × 4 phases = **64** indices (0–63) |
| Physical store size | **2048 slots × 2 bytes** = **4096 B** at Flash `$4000–$4FFF` |
| Unindexed slots | Indices 64–2047 read as `0x00` unless extended later |

The 4096-byte region is a **sparse physical container**: the macro ISA (`0x01–0x0A`) uses only the low 64 indices. Future extensions may widen the index without changing the Flash base.

- Output: **10-bit CW** — B9–B8 `REG_SEL`, B7–B0 per [microcode-spec.md](microcode-spec.md).
- Latch: **574 CW_L** + **574 CW_H** at execute edge.
- Not fetched via PC; **execute-phase** address mux drives Flash.

Pack / verify (archive prototype only): [prototype-flash-cw](../archive/prototype-flash-cw/README.md).

---

## 4. Boot segment

- Reset comb forces **`$FFFC`**; vector points to entry in **`$0000–$07FF`**.
- Bootloader: Mailbox READ → **LDIO + STA16** block-copy to **RAM `$0800+`** ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)).
- Product path: **`JMP $0800`** after SP/RP/GPR pre-init ([boot-rom.md](../fixtures/boot-rom.md)).
- Recovery path: RAM vector @ `$FFFC` + **HALT** (same boot image) → operator Run + RESET.

### 4.1 ROM layout (product image)

| CPU addr | Content |
|----------|---------|
| `$0000` | `JMP $0100` |
| `$0100` | POST, Mailbox READ poll |
| `$0120` | Unrolled copy (248× `LDIO`/`STA16`) + `JMP $0600` |
| `$00F0` | ROM constants (8-bit `LDA` reach) |
| `$0600` | GPR sanitize, SP/RP `STA16`, `JMP $0800` |

---

## 5. Utility segment

- Fixed assets in Flash; bootloader **shadows** to RAM (no software bank switch).
- Runtime may execute from RAM copies after Mode B + RESET.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | Single NOR; 3-segment model |
| 2026-06-01 | §3 index: 6-bit sparse map into CW region |
| 2026-06-10 | **v1.0** — 10b CW, 2048×2 B @ `$4000–$4FFF`; PDIP Flash |
