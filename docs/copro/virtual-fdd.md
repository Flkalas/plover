# Virtual FDD (S7a)

Virtual floppy disk device used by PL-DOS.

## Sector API

- Sector size: **512 bytes**
- Addressing: 0-based `sector_number`

## Host implementation

- `plover_vm/memory/vfdd.py` — `.img` file backed `read_sector`/`write_sector`
- `kern/vfdd.py` — driver wrapper used by higher layers (PLFS, loader)
- `kern/drives.py` / `crates/plover_os/src/drives.rs` — PL-DOS multi-drive manager (`mount`, `A:`/`B:` paths)

## Multi-drive (PL-DOS)

- Each drive letter maps to a separate `.img` with its own PLFS catalog.
- Mailbox `CMD_READ`/`WRITE` use `MB_AUX` as **drive_id** (0 = first mounted drive, typically `A:`).
- Shell: `mount B img`, `unmount B`, `drives`, `copy A:FILE B:FILE`.

## Gate

- `tests/test_vfdd_io.py`
- `tests/test_multi_drive.py`

