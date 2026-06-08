# Software memory layout (v0.1 VM)

**Related:** [memory-map.md](memory-map.md) · [software-roadmap.md](software-roadmap.md)

Normative RAM regions for Forth, kernel, PL-DOS on the 64 KiB map (`plover_vm` and target hardware).

## Global map

| Region | Range | Owner | Notes |
|--------|-------|-------|-------|
| Boot / vectors | `$0000–$07FF`, `$FFFC` | ROM | [bootloader.md](bootloader.md) · [boot-jmp-handoff.md](boot-jmp-handoff.md) |
| Kernel + Forth dict | `$0800–$27FF` | S3 / S6 | Entry @ `$0800` Run mode |
| **PLR load arena** | `$2800–$5FFF` | S7c | Spawn targets |
| Heap / FS cache | `$6000–$DFFF` | S6 / S7b | Bump allocator, dir window |
| Data stack | `$E000–$F5FF` | Forth | SP grows up |
| Return stack | `$F600–$FEEF` | Forth / CALL | RP grows up |
| TIB | `$1000–$10FF` | Forth | 256 B line buffer |
| Mailbox | `$FF00–$FFFB` | I/O | [mailbox-protocol.md](mailbox-protocol.md) |

## Forth cells (16-bit LE in RAM)

| Symbol | Address | Purpose |
|--------|---------|---------|
| `SP` | `$0E00` | Data stack pointer |
| `RP` | `$0F00` | Return stack pointer |
| `HERE` | `$0E02` | Dictionary / heap bump |
| `DP` | `$0E04` | Data pointer |

## PL-DOS fixed addresses

| Symbol | Value | Purpose |
|--------|-------|---------|
| `PLR_LOAD_BASE` | `$2800` | Default `.PLR` load |
| `FS_DIR_CACHE` | `$6000` | Mounted dir sector copy |
| `HEAP_BASE` | `$6100` | Kernel allocator |

Changes to these ranges require a doc revision and full regression (`pytest tests/`).
