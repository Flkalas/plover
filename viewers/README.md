# Viewers

Static HTML viewers for developer inspection. Not cited in `reference/**`.

| Viewer | Path | Source |
|--------|------|--------|
| **cyclesim-block** (KiCad-style functional-block schematic) | [cyclesim-block/alu8_func/index.html](cyclesim-block/alu8_func/index.html) | `python -m simulators.cyclesim export alu8 --html` |

Shared templates live under each viewer kind's `_assets/` folder. Generated `index.html` files embed the schematic SVG and search manifest inline so they open via `file://` without a local server.

## Regenerate alu8 block schematic

```bash
python -m simulators.cyclesim export alu8 --html
```

Output: `viewers/cyclesim-block/alu8_func/index.html`

Features: pan/zoom, net and symbol highlight, inspector panel, search by net or ref. Control nets (`bctrl`, `lgc`, `cin`, …) render in orange.
