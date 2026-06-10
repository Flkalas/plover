# ROM Architecture v0.1

**Related:** [system-architecture.md](system-architecture.md) · [memory-map.md](memory-map.md)

ROM is the **code of law** for the system: deterministic rules for boot, datapath control, and fixed assets.

---

## 1. Three segments (logical)

| Segment | Purpose | CPU visibility |
|---------|---------|----------------|
| **Control** | `{opcode, phase}` → **8-bit CW** | Execute phase only (separate Flash addr mux) |
| **Boot** | POST, bootloader, reset vector | Mode A: `$0000–$07FF`, `$FFFC` |
| **Utility** | Fonts, LUTs, fixed routines | ROM in Mode A; shadowed to RAM `$0800+` |

---

## 2. Physical device

**Single** `SST39SF010A-70-4C-PHE` — 128K×8 parallel NOR.

| Property | Rationale |
|----------|-----------|
| Parallel | Power-on execute — no SPI init |
| Single 8-bit | Matches TTL datapath; no Flash×2 glue |
| 128 KB | Boot + CW + fonts + headroom |

### Flash physical layout (draft)

| Flash offset | Content | CPU map (Mode A) |
|--------------|---------|------------------|
| `$0000–$07FF` | Boot + bootloader | `$0000–$07FF` ROM |
| `$0800–$3FFF` | Utility (fonts, tables) | Copy source |
| `$4000–$47FF` | **8b microcode store** (2048×8) | Exec addr `{opcode,phase}` |
| `$FFFC–$FFFF` | Reset vector image | `$FFFC` enclave |

Microcode base **`$4000`** is the packer default in `tools/pack_control_store.py`.

---

## 3. Control segment

**Addressing (v0.1 packer):**

```
store_index = ((opcode[3:0] << 2) | phase[1:0])   // 6 bits → 0..63
Flash_addr  = $4000 + store_index
```

| Property | Value |
|----------|-------|
| Logical index width | 6 bits (`opcode[3:0]` × `phase[1:0]`) |
| Active slots (v0.1 ISA) | 16 opcode nibbles × 4 phases = **64** indices (0–63) |
| Physical store size | **2048×8** bytes at Flash `$4000–$47FF` |
| Unindexed region | Indices 64–2047 read as `0x00` unless extended later |

The 2048-byte region is a **sparse physical container**: the v0.1 macro ISA (`0x01–0x0A`) uses only the low 64 indices. Future extensions may widen the index (e.g. full `opcode[7:0]`) without changing the Flash base.

- Output: **8-bit CW** — see [microcode-spec.md](microcode-spec.md).
- Not fetched via PC; **execute-phase** address mux drives Flash.

---

## 4. Boot segment

- Reset comb forces **`$FFFC`**; vector points to entry in **`$0000–$07FF`**.
- Bootloader: Mailbox READ → **LDIO + STA16** block-copy to **RAM `$0800+`** ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)).
- Product path: **`JMP $0800`** after SP/RP/GPR pre-init (`boot_rom.hex`).
- Recovery path: RAM vector @ `$FFFC` + **HALT** (`boot_rom_manual.hex`) → operator Run + RESET.

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
| 2026-06-01 | §3 index: 6-bit sparse map into 2048 B CW region |
