# ROM Architecture v1.0

**Related:** [system-architecture.md](system-architecture.md) · [memory-map.md](memory-map.md) · [microcode-spec.md](microcode-spec.md)

ROM is the **code of law** for the system: deterministic rules for boot, datapath control, and fixed assets.

---

## 1. Three segments (logical)

| Segment | Purpose | CPU visibility |
|---------|---------|----------------|
| **Control** | **CPLD pipe CU** | Pipe / EX strobes in ATF1504 |
| **Boot** | POST, bootloader, reset vector | Mode A: `$0000–$07FF`, `$FFFC` |
| **Utility** | Fonts, LUTs, fixed routines | ROM in Mode A; shadowed to RAM `$0800+` |

---

## 2. Physical device

**Single** `SST39SF010A-70-4C-PHE` — 128K×8 parallel NOR, **PDIP-32**.

| Property | Rationale |
|----------|-----------|
| Parallel | Power-on execute — no SPI init |
| Single 8-bit data bus | Matches TTL datapath |
| 128 KB | Boot + fonts + headroom |

### Flash physical layout

| Flash offset | Content | CPU map (Mode A) |
|--------------|---------|------------------|
| `$0000–$07FF` | Boot + bootloader | `$0000–$07FF` ROM |
| `$0800–$4FFF` | Utility (fonts, tables) | Copy source |
| `$FFFC–$FFFF` | Reset vector image | `$FFFC` enclave |

Control is entirely in the CPLD pipe CU ([microcode-spec.md](microcode-spec.md), [cpld-pipe-cu.md](cpld-pipe-cu.md)).

---

## 3. Control (CPLD pipe CU — normative v1.0)

Strobes come from the **ATF1504 pipe CU** — see [cpld-system-controller.md](cpld-system-controller.md) and [cpld-pipe-cu.md](cpld-pipe-cu.md).

ISA / SYS sheet: [microcode-spec.md](microcode-spec.md).

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
