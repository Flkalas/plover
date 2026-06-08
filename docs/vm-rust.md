# Plover VM Rust runtime (v0.1)

**Source:** [archive/gemini/rust_vm_migration_and_virtualization.md](archive/gemini/rust_vm_migration_and_virtualization.md)  
**Related:** [system-architecture.md](system-architecture.md), [mailbox-protocol.md](mailbox-protocol.md), [display-console.md](display-console.md)

Normative **Rust** implementation of the logic VM (`plover_vm`), replacing Python for integrated Presenter + multi-threaded audio. Python `plover_vm/` remains during transition as parity oracle.

---

## 1. Workspace crates

| Crate | Role |
|-------|------|
| `plover_mmu` | 64 KiB map decode, NOR/RAM, Mailbox MMIO bridge |
| `plover_copro` | VDU, APU, HID, vFDD Mailbox dispatch |
| `plover_core` | **micro/macro/fast** engines, `step_once`, `reset`, NOR/CW load, trace JSONL |
| `plover_presenter` | Host video compositor, HID bridge, APU mix (SDL2/cpal optional) |
| `plover_os` | PL-DOS: vFDD/PLFS, `.PLR` spawn, shell, kernel scenario, Python toolchain subprocess |
| `plover_forth` | Host Forth interpreter (S3) + optional Mailbox I/O words |
| `plover_scenario` | YAML runner: vdu/apu/hid/dos/kernel/forth + generic boot scenarios |
| `plover_vm` (bin) | CLI: `run`, `step`, `scenario`, `dos-shell`, `vdu-demo`, `apu-demo`, `hid-demo`, `play` |

**Stays Python:** `hwsim/`, `cyclesim/`, `plover_asm/`, `kern/` (oracle), `pytest tests/`.

---

## 2. Thread model (v0.1)

| Phase | Model |
|-------|-------|
| 1–2 | **Single-thread** — CPU step + Mailbox dispatch (Python parity) |
| 3+ | Presenter/audio threads read **snapshots** of `VduState`/`ApuState`; CPU thread owns Mailbox writes |

No full Atomic Mailbox in v0.1 — avoids races documented in Rust migration notes.

---

## 3. MODE_BOTH compositing (normative)

When `VDU_MODE = 2` (both):

1. **Bitmap layer** — 320×200 RGB565 from `GFX_*` commands.
2. **Text layer** — 40×25 cells, 8×8 px each; fg from attr low nibble, bg from high nibble via `text_palette`.
3. **Composite rule:** For each text cell pixel, if **fg palette index is 0** (transparent chroma), show **bitmap pixel** underneath; else show **text fg color**. Bg attr fills cell background before fg glyph pixels (non-transparent fg over bg).

Status bar: rows 200–239 (20 px) = solid border color `0x0000` unless extended later.

Presenter applies **2×2 nearest** upscale to 640×480 and **temporal 2× hold** at 60 Hz window (30 Hz content).

---

## 4. Dependencies

| Component | Crate feature |
|-----------|---------------|
| Core/MMU/copro | std only |
| Presenter window | `sdl` (SDL2) |
| Presenter audio | `audio` (cpal) |
| CI / headless | default — offscreen RGB buffer, no SDL |

Install Rust: [rustup.rs](https://rustup.rs). On **Windows**, use the default **`x86_64-pc-windows-msvc`** toolchain and install **Visual Studio Build Tools** (C++ workload) so `link.exe` is available:

```powershell
winget install -e --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Open a **Developer PowerShell for VS 2022** (or run `vcvars64.bat`) before `cargo` if a plain terminal cannot find the MSVC linker.

Build:

```bash
cargo test --workspace
cargo run -p plover_vm -- run hw/fixtures/sram/add_imm.sram.hex --map run --engine fast
cargo run -p plover_vm -- step --engine micro
cargo run -p plover_vm -- scenario hw/scenarios/vm/add_imm.yaml
cargo run -p plover_vm -- scenario hw/scenarios/vm/forth_boot.yaml
cargo run -p plover_vm -- dos-shell
cargo run -p plover_vm -- vdu-demo
```

**PL-DOS:** `plover_os` mirrors Python `kern/` + `plover_vm/dos_scenario.py`. Shell commands `dir`/`run`/`type`/`del`/`mon`/`plsrun`/`ccrun`/`ldrun` call Python `plover_asm`/`plover_cc`/`plover_ld` via subprocess (same as Python shell). Fixture `hw/fixtures/plr/hello.plr` is committed so boot does not require assembly at runtime.

---

## 5. Python deprecation

- `python -m plover_vm` prints deprecation notice pointing to `cargo run -p plover_vm`.
- Parity: Rust `cargo test` mirrors Python `test_vdu_*`, `test_apu_*`, `test_hid_*`, `test_forth_*`, generic/boot YAML scenarios, and `plover_os` shell tests mirror `test_dos_shell.py` (Python CLI remains regression oracle).

---

## Change log

| Date | Note |
|------|------|
| 2026-06-08 | v0.1 workspace; MODE_BOTH chroma-key compositing |
| 2026-06-08 | `plover_os` + `dos-shell` + `kind: dos` scenario |
| 2026-06-08 | Full CLI port: 3 engines, `step`, demos, `plover_forth`, generic/kernel scenarios |
