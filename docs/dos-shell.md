# PL-DOS shell (S7d)

PL-DOS uses a small command shell on top of PLFS + `.PLR` loader.

**Display:** normative **40×25** text — [display-console.md](display-console.md). v0.1 VM uses the host terminal; target hardware uses RP2350 HDMI.

In v0.1 bring-up the shell is represented by a scripted scenario that exercises:

- `dir` (list directory)
- `run <file>` (spawn `.PLR`)

## Gate

- `hw/scenarios/vm/dos_boot.yaml`
- `tests/test_dos_shell.py`
- `python tools/run_dos_demo.py`

## Rust (plover_os)

```bash
cargo test -p plover_os
cargo run -p plover_vm -- dos-shell
cargo run -p plover_vm -- scenario hw/scenarios/vm/dos_boot.yaml
```

Interactive shell: prompt `PL-DOS>`, lines truncated to 40 characters (Python parity). `plsrun`/`ccrun`/`ldrun` require Python on `PATH`.

