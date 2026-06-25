# BASIC system (Tiny BASIC + game)

**Related:** [runtime-api.md](runtime-api.md) · [game-api.md](game-api.md) · [software-memory-layout.md](software-memory-layout.md)

Student-facing Tiny BASIC with PC and game builtins on the 8-bit Plover VM.

## Workflow

1. Edit `game.bas` (line numbers, one statement per line).
2. Host tokenizes: `python basic/tokenize.py game.bas game.tok`
3. Run: `cargo run -p plover_vm --features sdl,audio -- play --basic game.bas --headless`

The token VM (`plover_basic::BasicVm`) reads bytecode at **`$2800`**. Variables **`A`–`Z`** live at **`$0E10`–`$0E29`**.

## PC commands

| Statement | Example |
|-----------|---------|
| `PRINT` | `10 PRINT "HELLO"` |
| `LET` | `20 LET X = 50` |
| `GOTO` | `30 GOTO 10` |
| `CLS` | `40 CLS` |
| `INKEY()` | `50 K = INKEY()` |
| `IF … THEN GOTO` | `60 IF INKEY() <> 32 THEN GOTO 40` |
| `LET X = X + n` | `70 LET X = X + 2` |

## Game commands

| Statement | Example |
|-----------|---------|
| `SPRITE` | `SPRITE 0, X, Y, 1, 0` |
| `DRAW` | `DRAW` (flush tilemap + OAM) |
| `SOUND` | `SOUND 0, 440, 5` |
| `LAYER` | `LAYER 0, 1, 0` (scroll dx, dy) |
| `TILE` | `TILE 0, 0, 0, 1` |

Variables in `SPRITE` must be single letters (`X`, `Y`, not `PX`).

## Example programs

- [`hw/fixtures/basic/pong.bas`](../hw/fixtures/basic/pong.bas) — move sprite with space bar
- [`hw/fixtures/basic/shooter.bas`](../hw/fixtures/basic/shooter.bas) — layer + multiple sprites

## Limits (v0.1)

- No `DATA`/`READ`, arrays, floats, or `INCLUDE`
- Host tokenizer only (no on-CPU parser)
- ~30 Hz frame rate via `DRAW` + presenter
