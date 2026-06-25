# PL-DOS shell (S7d)

PL-DOS uses a small command shell on top of PLFS + `.PLR` loader.

**Display:** normative **40×25** text — [display-console.md](../copro/display-console.md). v0.1 VM uses the host terminal; target hardware uses RP2350 HDMI.

In v1.0 breadboard bring-up (M1–M5) the shell is represented by a scripted scenario that exercises:

- `dir` (list directory)
- `run <file>` (spawn `.PLR`)
- Multi-drive: `mount` / `unmount` / `drives`, `B:` switch, `copy A:FILE B:FILE`, `dir B:`

## Gate

- `hw/scenarios/vm/dos_boot.yaml`
- `hw/scenarios/vm/dos_multidrive.yaml`
- `tests/test_dos_shell.py`
- `tests/test_multi_drive.py`
- `python tools/run_dos_demo.py`

## Rust (plover_os)

```bash
cargo test -p plover_os
cargo run -p plover_vm -- dos-shell
cargo run -p plover_vm --features sdl -- dos-shell --gui
cargo run -p plover_vm -- scenario hw/scenarios/vm/dos_boot.yaml
```

Interactive shell: prompt `A>` (current drive), lines truncated to 40 characters (Python parity). `plsrun`/`ccrun`/`ldrun` require Python on `PATH`.

**GUI (`--gui`, SDL):** 640×480 window mirrors VDU text (kernel boot + shell output). **Click the window** and type commands there (`dir`, `help`, `exit`). Terminal echo remains for copy/paste.

