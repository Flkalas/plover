# Frozen fixtures (breadboard burn)

**Status:** Frozen 2026-07-04 — no toolchain in the active repository. Burn these byte images to Flash/SRAM as described in [M4b-boot-hardware.md](../hw-bringup/M4b-boot-hardware.md).

| File | Target | Use |
|------|--------|-----|
| [boot-vector.md](boot-vector.md) | Flash `$FFFC` | Reset vector (4 bytes) |
| [boot-rom.md](boot-rom.md) | Flash `$0000+` | Bootloader + utilities |
| [add_imm-sram.md](add_imm-sram.md) | SRAM `$0800` | First-program smoke (ADD imm) |

Format: one **hex byte per line** (e.g. `05` = `0x05`). When programming, convert to your programmer’s format (byte stream or Intel HEX).

Historical generators and full `hw/fixtures/` tree: see [archived-code-guide.md](../../developer/archived-code-guide.md) → `hw.tar.gz`.
