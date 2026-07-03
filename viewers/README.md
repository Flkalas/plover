# Viewers

Static HTML viewers for developer inspection. Not cited in `reference/**`.

| Viewer | Path | Source |
|--------|------|--------|
| **cyclesim-block** (functional-block netlist) | [cyclesim-block/alu8_func/index.html](cyclesim-block/alu8_func/index.html) | `python -m simulators.cyclesim export alu8 --html` |

Shared templates live under each viewer kind's `_assets/` folder. Generated `index.html` files embed data inline so they open via `file://` without a local server.

## Regenerate alu8 block viewer

```bash
python -m simulators.cyclesim export alu8 --html
```

Output: `viewers/cyclesim-block/alu8_func/index.html`
