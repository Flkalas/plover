# Phase1 datapath interactive viewer

Browser UI for **v0.2 Phase1** — CW digital inputs, gate-level hwsim, datapath diagram, waveforms, and wiring.

## Quick start

```bash
# Generate probe-rich netlist (once after clock netlist changes)
python tools/gen_p1_view_netlist.py

# Start server (default http://127.0.0.1:8765/)
python -m hwsim serve
```

Open the URL printed in the terminal.

## What it shows

| Panel | Content |
|-------|---------|
| **CW inputs** | `alu_op`, `src_reg`, `dst_reg`, `bus_en` — queue cycles or use preset |
| **Datapath** | CW → decode → MUX → ALU → regfile; CMP CP mask |
| **Outputs** | R0–R3 hex, ALU Y, `cmp_n` |
| **Waves** | Grouped probes, zoom window, time cursor |
| **Wiring** | Filtered `export_svg` (regfile, MUX, ALU, decode) |

Simulation uses [`cpu_datapath_p1_view.yaml`](../hw/netlist/blocks/cpu_datapath_p1_view.yaml) (2 MHz clock from OSC+74).

## Presets

| ID | Cycles | Expected R2 |
|----|--------|-------------|
| `clock_add_demo` | INC R0, INC R2×2, ADD | `0x02` |

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/meta` | opcodes, presets, probe list |
| GET | `/api/wiring-filtered.svg` | Schematic pin list (filtered) |
| POST | `/api/simulate` | `{ "preset": "clock_add_demo" }` or `{ "preset": "custom", "cycles": [...] }` |

## Regression

```bash
python -m hwsim run hw/tests/p1_viewer_demo.yaml
python -m hwsim run --all
```

## Related

- [hw-bringup-p1-datapath.md](hw-bringup-p1-datapath.md) — Phase1 scope
- [hw/viewer/](../hw/viewer/) — static artifact inspector (no server)
- [hw-sim.md](hw-sim.md) — hwsim CLI
