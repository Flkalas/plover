# Game API tutorial

**Related:** [basic-system.md](basic-system.md) · [mailbox-protocol.md](../copro/mailbox-protocol.md) · [display-console.md](../copro/display-console.md)

Quick guide for sprites, layers, and sound from BASIC.

## Sprites (OAM)

Each sprite is 8×8, palette index 0–15. Up to **32** sprites (id 0–31).

```basic
10 LET X = 50
20 LET Y = 90
30 SPRITE 0, X, Y, 1, 0
40 DRAW
```

- **tile** — solid fill color index in the sprite’s palette (see `GFX` v0.2)
- **pal** — palette bank 0–15
- Call **`DRAW`** after updating sprites to composite the frame

Hide a sprite (from assembly / future BASIC): `GFX_OAM_HIDE`.

## Layers

Two scrollable tile layers (40×25 tiles, 8×8 px):

```basic
10 LAYER 0, 1, 0
20 TILE 0, 0, 0, 1
30 TILE 0, 1, 0, 2
40 DRAW
```

- **LAYER n, dx, dy** — scroll layer `n` (0 or 1)
- **TILE layer, tx, ty, id** — place tile id at tile coordinates

Text HUD uses the existing VDU text layer (`MODE_BOTH`).

## Palette

Set tile palette entries via `rt_pal_set` / `GFX_SET_TILE_PAL`. The play bootstrap sets a few default colors (red, green, yellow) on palette 0.

## Sound

Four PSG channels (square wave):

```basic
10 SOUND 0, 440, 5
```

- **ch** — 0–3
- **freq** — Hz
- **dur** — duration in tenths of a second (approximate)

Use `--audio` with `play` for host output.

## Game loop pattern

```basic
10 LET X = 20
20 SPRITE 0, X, Y, 3, 0
30 DRAW
40 IF INKEY() <> 32 THEN GOTO 30
50 LET X = X + 2
60 GOTO 20
```

Press **space** (ASCII 32) to move in this pattern (`IF INKEY() <> 32` skips movement when space is held).

## Headless gate

`hw/scenarios/vm/basic_boot.yaml` loads `pong.bas`, runs token steps, and checks title text + initial `X` variable.
