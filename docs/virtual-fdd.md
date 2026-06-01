# Virtual FDD (S7a)

Virtual floppy disk device used by PL-DOS.

## Sector API

- Sector size: **512 bytes**
- Addressing: 0-based `sector_number`

## Host implementation

- `plover_vm/memory/vfdd.py` — `.img` file backed `read_sector`/`write_sector`
- `kern/vfdd.py` — driver wrapper used by higher layers (PLFS, loader)

## Gate

- `tests/test_vfdd_io.py`

