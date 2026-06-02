# Plover hwsim — electrical timing simulator

Event-driven block-level simulator for **74HC TTL comb paths**. **Python 3.10+ stdlib only** — no pip, no make, no Verilog.

## Scope (what hwsim is / is not)

| Layer | Tool | Notes |
|-------|------|-------|
| **74HC ALU / decode** | **hwsim** | Datasheet `t_pd`, operand→Y slack @ 2 MHz budget |
| **574 latch (one CP ↑)** | **hwsim** | Manual `net_clk` pulse — [`alu_b3_latch`](hw/tests/alu_b3_latch.yaml) |
| **CPLD decode** | **hwsim ideal** | `CPLD_SYSTEM_CTRL` **t_pd=0** — comb truth table only |
| **Micro-phases, CW, flags, branches** | **[plover_vm](../plover_vm/)** | Flash CW, `REG_WE`, `Y_OE`, CMP/BEQ |
| **OSC / ÷2 / 2 MHz recurring** | **not hwsim** | RAM blow-up; validate on **scope** at B3c bring-up |
| **Continuous clock + full ALU** | **blocked** | `alu_b3_clock` netlists rejected by CLI |

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
| `python -m hwsim run --all` | All tests in `hw/tests/` (17) |
| `python -m hwsim report <build_dir>` | Regenerate HTML from JSON artifacts |
| `python -m hwsim export-svg <netlist.yaml> [-o out.svg]` | Wiring diagram SVG |
| `python -m hwsim pinout <74HC283>` / `pinout --list` | DIP pin map ([`hw/pinout/`](../hw/pinout/)) |
| `python -m hwsim export-schematic <netlist.yaml> [--html]` | DIP schematic; `alu8` → **14 DIP** assembly layout; `--logical` = hwsim instances; `--html` = drag chips, net hubs, wire bends |
| `python -m hwsim diff-kicad <kicad.net> <netlist.yaml>` | Compare KiCad export vs YAML |

Outputs go to `build/hwsim/<test_name>/`:

- `waves.json` — probe waveforms
- `timing_report.json` — slack, violations, checks
- `report.html` — standalone summary
- `wiring.svg` — block diagram (from netlist)

Open [`hw/viewer/index.html`](../hw/viewer/index.html) in a browser and load these files.

## Assumptions

- 5 V, 25 °C, datasheet typ/max delays (74HC); **CPLD/MMIO ideal (0 ns)** in [`hw/timing/cpld.yaml`](../hw/timing/cpld.yaml)
- **No net delay** (parasitic L/C excluded)
- Combinational: inertial delay on outputs
- Sequential: setup/hold check at **single** clock edge (stimulus), not free-running OSC

## ALU netlist regeneration (Phase B2)

After changing [`tools/alu8_cases.py`](../tools/alu8_cases.py) or [`tools/gen_alu8_netlist.py`](../tools/gen_alu8_netlist.py), run from repo root:

```bash
python tools/gen_alu_decode_netlist.py
python tools/gen_alu8_netlist.py
python tools/gen_alu_b3_netlist.py
python tools/gen_alu8_full_test.py
python tools/gen_alu8_opcode_timing.py
python tools/gen_opcode_cheatsheet.py
python -m hwsim run --all
```

(`gen_alu_b3_clock_netlist.py` only updates wiring YAML for breadboard — **no hwsim clock test**.)

## File layout

| Path | Role |
|------|------|
| [`hw/netlist/blocks/`](../hw/netlist/blocks/) | Block netlists (ALU, CPU gate) |
| [`hw/timing/`](../hw/timing/) | Datasheet delay tables |
| [`hw/models/`](../hw/models/) | Chip behavior metadata |
| [`hw/pinout/`](../hw/pinout/) | DIP physical pin maps (datasheet) |
| [`hw/tests/`](../hw/tests/) | Stimulus + checks |
| [`hwsim/`](../hwsim/) | Simulator source |

## Tests (17)

### CPU gate (5)

| Test | Block | Focus |
|------|-------|-------|
| `cpld_gpr_decode` | cpld_system_ctrl | ADD Reg_Sel + LOAD_R* (ideal CPLD) |
| `regfile_574` | regfile_574 | 574×4 dual-read GPR |
| `mem_decode` | sram256_dual | Mode A/B, mailbox, A15 bank |
| `monitor_poll` | sram256_dual | MMIO STATUS poll stub |
| `boot_handoff` | cpld_system_ctrl | Reset $FFFC + Run mode |

### ALU bringup (12)

| Test | Block | Focus |
|------|-------|-------|
| `alu283_carry` | alu283 | 8-bit carry cascade |
| `alu8_full` / `alu8_timing` / `alu8_opcode_timing` | alu8 | 12-opcode functional + per-opcode slack |
| `alu8_cmp_sub` | alu8 | CMP flags from SUB (`Y==0`, `net_c_hi`) |
| `cmp_y_oe_bus` | cmp_y_oe_bus | `Y_OE=1` → `net_d` follows `net_y`; `Y_OE=0` → bus Z |
| `alu_decode_full` / `alu_decode_timing` | alu8_decode | CW → control nets |
| `alu_b3_sub_critical` / `alu_b3_xor_critical` / `alu_b3_inc_dec` / `alu_b3_latch` | alu_b3 | B3 comb + **one** 574 latch edge |

**B3c 2 MHz:** real hardware + oscilloscope — not hwsim. See [hw-bringup-b3.md](hw-bringup-b3.md) §B3c.

Full ALU wiring: [alu8.md](../hw/netlist/blocks/alu8.md).

## BOM part → model

Supported parts: `74HC74` (manual CP only in tests), `74HC04`, `74HC283`, `74HC574`, `74HC161`, `74HC157`, `74HC245`, gates `74HC08/32/86`, mux `74HC151/153`, **`ALU_153_SLICE`**, **`ALU_Y_MUX_SEL`**, **`ALU_CMP_SUB`**, **`Y_BUS_BUF`**, **`CPLD_SYSTEM_CTRL` / `ATF1504AS`** (ideal), **`REGFILE_574_GPR`**, **`MAILBOX_MMIO`**.

`OSC_4M` exists for netlist validate / wiring export only — **do not run timing tests** with recurring OSC.

## Related

- [BOM.md](../BOM.md) — shopping list (5 V breadboard) · [bom-maintenance.md](bom-maintenance.md) — BOM audit/history · [purchase-devicesmart.md](purchase-devicesmart.md) — orders
- [alu-opcodes-timing.md](alu-opcodes-timing.md) — opcode slack table
- [microcode-spec.md](microcode-spec.md) — CW / phases (VM)
- [hw-bringup-b3.md](hw-bringup-b3.md) — breadboard bring-up
