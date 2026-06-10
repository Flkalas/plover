# Runtime API (`rt_*`)

**Related:** [mailbox-protocol.md](../copro/mailbox-protocol.md) · [basic-system.md](basic-system.md) · [software-memory-layout.md](software-memory-layout.md)

Normative CPU-side syscall library for BASIC, Forth, and Subset C. All graphics/audio go through Mailbox v0.2.

## Memory map

| Region | Range | Purpose |
|--------|-------|---------|
| Vector table | `$1000–$101F` | 16-bit LE entry addresses |
| `rt_*` code | `$1000–$17FF` | Syscall implementations |
| BASIC VM (reserved) | `$1800–$1FFF` | `basic_vm.pls` entry stub |
| Token program | `$2800+` | Host-compiled `.tok` |
| Variables A–Z | `$0E10–$0E29` | 26×8-bit (Tiny BASIC) |

## Calling convention

- **Registers:** `R0`–`R3` (`regs[0..4]`) hold arguments.
- **Entry:** `CALL rt_*` or indirect via vector table at `$1000`.
- **Return:** `RET` (caller’s return stack).

## PC layer

| BASIC | `rt_*` | Mailbox |
|-------|--------|---------|
| `CLS` | `rt_cls` | `VDU_CLS` (`0x10`) |
| `PRINT` | `rt_print_str` | `VDU_PRINT` (`0x14`) — R0=len, string in `MB_BUFFER` |
| `INPUT` | `rt_input_num` | `HID_KEY_READ` (planned) |
| `PEEK`/`POKE` | `rt_peek`/`rt_poke` | CPU RAM |
| `VSYNC` | `rt_vsync` | `VDU_VSYNC` (`0x30`) |

## Game layer

| BASIC | `rt_*` | Mailbox |
|-------|--------|---------|
| `SPRITE` | `rt_sprite_set` | `GFX_OAM_WRITE` (`0x2A`) — R0=id, R1=x, R2=y, R3=tile |
| `SPRITE OFF` | `rt_sprite_hide` | `GFX_OAM_HIDE` (`0x2B`) |
| `LAYER` | `rt_layer_scroll` | `GFX_LAYER_CFG` (`0x28`) |
| `TILE` | `rt_tile_set` | `GFX_TILEMAP_SET` (`0x29`) |
| `PALETTE` | `rt_pal_set` | `GFX_SET_TILE_PAL` (`0x27`) |
| `SOUND` | `rt_sound_play` | `APU_NOTE_ON` (`0x54`) + `APU_CH_SYNC` |
| `DRAW` | `rt_frame_flush` | `GFX_FRAME_FLUSH` (`0x2C`) |

## Source

- Assembly: [`hw/fixtures/sw/rt_lib.pls`](../hw/fixtures/sw/rt_lib.pls)
- Rust host parity: [`crates/plover_basic/src/runtime.rs`](../crates/plover_basic/src/runtime.rs)
- Smoke scenario: [`hw/scenarios/vm/rt_lib_smoke.yaml`](../hw/scenarios/vm/rt_lib_smoke.yaml)

## Vector table (v0.1)

| Offset | Symbol |
|--------|--------|
| `$1000` | `vec_rt_cls` → `rt_cls` |
| `$1002` | `vec_rt_print_str` |
| `$1004` | `vec_rt_vsync` |
| `$1006` | `vec_rt_sprite_set` |
| `$1008` | `vec_rt_frame_flush` |
| `$100A` | `vec_rt_sound_play` |
