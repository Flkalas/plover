# PL-DOS roadmap (S7)

PL-DOS is the final integration milestone on top of the VM stack (S1–S6): vFDD storage, a flat catalog filesystem, a `.PLR` loader, and a Forth shell.

**Related:** [software-memory-layout.md](software-memory-layout.md) · [mailbox-protocol.md](mailbox-protocol.md) · [rp2350-coprocessor.md](rp2350-coprocessor.md) · [display-console.md](display-console.md)

## Milestones

| ID | Goal | Gate |
|----|------|------|
| S7a | vFDD sector read/write API | `tests/test_vfdd_io.py` |
| S7b | PLFS flat catalog filesystem | `tests/test_fat_fs.py` |
| S7c | `.PLR` loader + spawn | `tests/test_plr_exec.py` |
| S7d | PL-DOS shell + `dos_boot.yaml` | `tests/test_dos_shell.py` |

## `.PLR` format (normative)

```
+0  magic[4]  \"PLR\\x00\"
+4  load_addr u16 LE
+6  byte_size u16 LE
+8  entry_off u16 LE
+10 code[byte_size]
```

Default `load_addr` should be `PLR_LOAD_BASE = $2800`. See [software-memory-layout.md](software-memory-layout.md).

## Filesystem (PLFS v0.1)

Flat catalog (no fragmentation) entry fields:

- `name[11]` (8.3 upper, padded)
- `start_sector u16`
- `size_bytes u16`
- `attr u8`

The v0.1 data area stores files as contiguous sector runs.

