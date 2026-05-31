# Memory Map v0.1

**Related:** [cpld-system-controller.md](cpld-system-controller.md) · [mailbox-protocol.md](mailbox-protocol.md)

---

## 1. CPU address space (16-bit)

| Range | Mode A (Boot) | Mode B (Run) | Notes |
|-------|---------------|--------------|-------|
| `$0000–$07FF` | **Boot ROM** (2 KB) | RAM | SST39 low window |
| `$0800–$FEFF` | RAM | RAM | Kernel, data, stack |
| `$FF00–$FFFB` | **Mailbox** (252 B) | Mailbox | Full A15–A0 decode |
| `$FFFC–$FFFF` | **ROM vector** | **RAM vector** | Never Mailbox |

**Decode priority:** `MAILBOX_EN` wins for `$FF00–$FFFB` only. `$FFFC–$FFFF` is excluded from mailbox.

---

## 2. Physical RAM — 2× IS62C256AL

| Chip | `/CE` condition | CPU range |
|------|---------------|-----------|
| **RAM_1** | `A15=0` | `$0000–$7FFF` |
| **RAM_2** | `A15=1` ∧ ¬`MAILBOX_EN` | `$8000–$FFFF` (except mailbox window) |

See CPLD pseudo-VHDL in [cpld-system-controller.md](cpld-system-controller.md).

---

## 3. MAP_MODE (operator manual)

| MAP_MODE | Switch | `$0000–$07FF` | `$FFFC–$FFFF` |
|----------|--------|---------------|---------------|
| 0 | **Boot** | ROM | ROM |
| 1 | **Run** | RAM | RAM |

No automatic map switch from software — operator toggles DIP, then **RESET**.

---

## 4. Flash (SST39) vs CPU map

| Access | Address source |
|--------|----------------|
| Instruction fetch (Mode A boot) | PC → `$0000–$07FF` / `$FFFC` via CPLD |
| Microcode CW | `{opcode, phase}` → Flash `$4000+` |
| Utility read | PC or boot copy loops |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-01 | 64 KB A15 bank; mailbox window |
