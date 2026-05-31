# Plover hwsim — electrical timing simulator

Event-driven block-level simulator for 74HC netlists. **Python 3.10+ stdlib only** — no pip, no make, no Verilog.

## Quick start

From repository root:

```bash
python -m hwsim run --all
```

## Commands

| Command | Description |
|---------|-------------|
| `python -m hwsim validate <netlist.yaml>` | BOM/pin/net checks |
| `python -m hwsim run <test.yaml>` | Run one timing test |
| `python -m hwsim run --all` | All tests in `hw/tests/` |
| `python -m hwsim report <build_dir>` | Regenerate HTML from JSON artifacts |
| `python -m hwsim export-svg <netlist.yaml> [-o out.svg]` | Wiring diagram SVG |
| `python -m hwsim diff-kicad <kicad.net> <netlist.yaml>` | Compare KiCad export vs YAML |

Outputs go to `build/hwsim/<test_name>/`:

- `waves.json` — probe waveforms
- `timing_report.json` — slack, violations, checks
- `report.html` — standalone summary
- `wiring.svg` — block diagram (from netlist)

Open [`hw/viewer/index.html`](../hw/viewer/index.html) in a browser and load these files.

## Assumptions

- 5 V, 25 °C, datasheet typ/max delays
- **No net delay** (parasitic L/C excluded)
- Combinational: inertial delay on outputs
- Sequential: setup/hold check at clock edge

## File layout

| Path | Role |
|------|------|
| [`hw/netlist/blocks/`](../hw/netlist/blocks/) | Block netlists |
| [`hw/timing/`](../hw/timing/) | Datasheet delay tables |
| [`hw/models/`](../hw/models/) | Chip behavior metadata |
| [`hw/tests/`](../hw/tests/) | Stimulus + checks |
| [`hwsim/`](../hwsim/) | Simulator source |

## BOM part → model

Supported parts in MVP: `OSC_4M`, `74HC74`, `74HC04`, `74HC283`, `74HC574`, `74HC161`, `74HC157`, `74HC245`, `74HC138`, gates `74HC08/32/86`, mux `74HC153`. Full ALU: [alu8.md](../hw/netlist/blocks/alu8.md).

## Related

- [BOM.md](../BOM.md) — physical parts
- [roadmap-next.md](roadmap-next.md) — hardware track B1–B3
- Verilog [`rtl/`](../rtl/) — separate track (not used by hwsim)
