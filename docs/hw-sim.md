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
| [`hw/netlist/blocks/`](../hw/netlist/blocks/) | Block netlists (ALU, CPU gate) |
| [`hw/timing/`](../hw/timing/) | Datasheet delay tables |
| [`hw/models/`](../hw/models/) | Chip behavior metadata |
| [`hw/tests/`](../hw/tests/) | Stimulus + checks |
| [`hwsim/`](../hwsim/) | Simulator source |

## Tests (15)

### CPU gate (5)

| Test | Block | Focus |
|------|-------|-------|
| `cpld_gpr_decode` | cpld_system_ctrl | ADD Reg_Sel + LOAD_R* |
| `regfile_574` | regfile_574 | 574×4 dual-read GPR |
| `mem_decode` | sram256_dual | Mode A/B, mailbox, A15 bank |
| `monitor_poll` | sram256_dual | MMIO STATUS poll stub |
| `boot_handoff` | cpld_system_ctrl | Reset $FFFC + Run mode |

### ALU bringup (10)

| Test | Block | Focus |
|------|-------|-------|
| `alu283_carry` | alu283 | 8-bit carry cascade |
| `alu8_full` / `alu8_timing` | alu8 | 12-opcode functional + slack |
| `alu_decode_full` / `alu_decode_timing` | alu8_decode | CW → control nets |
| `alu_b3_sub_critical` / `alu_b3_xor_critical` / `alu_b3_inc_dec` / `alu_b3_latch` | alu_b3 | B3 phased paths |
| `bringup_b3c_clock` | alu_b3_clock | B3c + 2 MHz clock |

Full ALU wiring: [alu8.md](../hw/netlist/blocks/alu8.md).

## BOM part → model

Supported parts: `OSC_4M`, `74HC74`, `74HC04`, `74HC283`, `74HC574`, `74HC161`, `74HC157`, `74HC245`, gates `74HC08/32/86`, mux `74HC151/153`, **`CPLD_SYSTEM_CTRL` / `ATF1504AS`**, **`REGFILE_574_GPR`**, **`MAILBOX_MMIO`**.

## Related

- [BOM.md](../BOM.md) — full procurement list · [purchase-devicesmart.md](purchase-devicesmart.md) — order history
- [roadmap-next.md](roadmap-next.md) — bring-up track
- [hw-bringup-b3.md](hw-bringup-b3.md) — bench wiring guide

---

## Plover Logic VM (`plover_vm/`)

Functional **logic simulator** with built-in NOR/RAM/Mailbox — runs whole programs without ns timing. Complements hwsim.

```bash
python -m pytest tests/ -q
python -m plover_vm run hw/fixtures/sram/add_imm.sram.hex --engine fast --map boot
python -m plover_vm scenario hw/scenarios/vm/boot_run.yaml
```

| Engine | Description |
|--------|-------------|
| `micro` | 8b CW micro-phases (default faithful) |
| `macro` | Same as micro via MacroEngine |
| `fast` | Direct ISA semantics (bring-up) |

Spec: [system-architecture.md](system-architecture.md) · Package: [`plover_vm/`](../plover_vm/)
