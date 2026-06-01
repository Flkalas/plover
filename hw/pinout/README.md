# 74HC DIP pin maps (Plover BOM)

Physical **DIP** pin numbers for breadboard parts in [BOM.md](../../BOM.md).  
Logical connectivity remains in [`hw/netlist/blocks/`](../netlist/blocks/) and [`hw/models/`](../models/).

## Layout convention

- **View:** package top, notch up, pin **1** at lower-left, numbering **counter-clockwise** (JEDEC DIP).
- **Symbols:** primary names match TI/NXP datasheets; `aliases` list vendor variants.
- **hwsim netlist** uses logical pin names (`A0`, `1Y`, `S`, …) — see `plover_netlist` in each file where mapping differs.

## Index

| Part | Package | File |
|------|---------|------|
| 74HC283 | DIP-16 | [dip/74hc283.dip16.yaml](dip/74hc283.dip16.yaml) |
| 74HC153 | DIP-16 | [dip/74hc153.dip16.yaml](dip/74hc153.dip16.yaml) |
| 74HC157 | DIP-16 | [dip/74hc157.dip16.yaml](dip/74hc157.dip16.yaml) |
| 74HC86 | DIP-14 | [dip/74hc86.dip14.yaml](dip/74hc86.dip14.yaml) |
| 74HC08 | DIP-14 | [dip/74hc08.dip14.yaml](dip/74hc08.dip14.yaml) |
| 74HC32 | DIP-14 | [dip/74hc32.dip14.yaml](dip/74hc32.dip14.yaml) |
| 74HC04 | DIP-14 | [dip/74hc04.dip14.yaml](dip/74hc04.dip14.yaml) |
| 74HC574 | DIP-20 | [dip/74hc574.dip20.yaml](dip/74hc574.dip20.yaml) |
| 74HC161 | DIP-16 | [dip/74hc161.dip16.yaml](dip/74hc161.dip16.yaml) |
| 74HC245 | DIP-20 | [dip/74hc245.dip20.yaml](dip/74hc245.dip20.yaml) |
| 74HC74 | DIP-14 | [dip/74hc74.dip14.yaml](dip/74hc74.dip14.yaml) |
| 74HC14 | DIP-14 | [dip/74hc14.dip14.yaml](dip/74hc14.dip14.yaml) |
| 74HC595 | DIP-16 | [dip/74hc595.dip16.yaml](dip/74hc595.dip16.yaml) |

Full list: [index.yaml](index.yaml). Schema: [schema.yaml](schema.yaml).

## CLI

```bash
python -m hwsim pinout 74HC283
python -m hwsim pinout --list
```

## Sources

Pin tables are taken from manufacturer datasheets (NXP, Texas Instruments), rev. as linked in each YAML `sources` block.  
**SN74LVC** TSSOP parts on [BOM-3v3.md](../../BOM-3v3.md) use the **same logic pin names**; only the package pin numbers differ — add `dip/` or `tssop/` files when PCB layout is fixed.

## Schematic (DIP + wires)

```bash
python -m hwsim export-schematic hw/netlist/blocks/alu8.yaml -o build/alu8-schematic.svg --html
```

Opens in browser: `build/alu8-schematic.html` or [`hw/viewer/schematic.html`](../viewer/schematic.html).

Power: **VCC** (red, top rail) and **GND** (gray, bottom rail) — all `pwr_vcc` / `pwr_gnd` ties shown.

## Related

- Block wiring (nets): `python -m hwsim export-svg hw/netlist/blocks/alu8.yaml`
- Behavioral pins: [`hw/models/`](../models/)
- KiCad naming: [docs/hw-schematic.md](../../docs/hw-schematic.md)
