# Viewers

Static HTML viewers for developer inspection. Not cited in `reference/**`.

| Viewer | Path | Source |
|--------|------|--------|
| **cyclesim-block** (12-DIP ALU schematic) | [cyclesim-block/alu8_func/index.html](cyclesim-block/alu8_func/index.html) | `python -m simulators.cyclesim export alu8 --html` |

Shared templates live under each viewer kind's `_assets/` folder. Generated `index.html` files embed the schematic SVG and search manifest inline so they open via `file://` without a local server.

## Regenerate alu8 schematic

```bash
python -m simulators.cyclesim export alu8 --html
```

Output: `viewers/cyclesim-block/alu8_func/index.html`

Shows **12 physical DIP** (`U_ALU_153_0..7`, `U_ALU_283_LO/HI`, `U_ALU_157_YBP_0/1`). CPLD-driven control nets and CMP flags appear as **global port labels** only (no behavioral glue symbols).

Features: pan/zoom, net and symbol highlight, inspector panel, search by net or ref. Control nets render in orange.
