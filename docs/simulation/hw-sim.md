# Plover hwsim — electrical timing simulator

Event-driven block-level simulator for **74HC TTL comb paths**. **Python 3.10+ stdlib only** — no pip, no make, no Verilog.

## Truth hierarchy (verification stack)

**hwsim is the source of truth** for gate-level behavior on YAML netlists (including ideal CPLD @ 0 ns). Shared tables and comb logic live under [`hw/micro/`](../hw/micro/) and [`hw/logic/`](../hw/logic/).

| Layer | Tool | Aligns to |
|-------|------|-----------|
| Electrical + slack | **hwsim** | Datasheet `t_pd`, netlist YAML |
| Structural @ micro phase | [cyclesim](../cyclesim/) | Same netlist + `hw/logic` (zero delay) |
| ISA / programs | [plover_vm](../plover_vm/) | cyclesim phase semantics + microcode-spec |

When cyclesim and plover_vm disagree, **cyclesim wins** (hwsim-backed netlist). When cyclesim and hwsim disagree on comb meaning, **hwsim wins**.

## Scope (what hwsim is / is not)

| Layer | Tool | Notes |
|-------|------|-------|
| **74HC ALU / decode** | **hwsim** | Datasheet `t_pd`, operand→Y slack @ 2 MHz budget |
| **Gate netlist @ micro phase** | **[cyclesim](../cyclesim/)** | Zero-delay comb + 574 CP↑ |
| **574 latch (one CP ↑)** | **hwsim** | Manual `net_clk` pulse — [`alu_b3_latch`](hw/tests/alu_b3_latch.yaml) |
| **CPLD GPR** | **hwsim ideal** | `CPLD_GPR_CTRL` — GPR decode from `REG_SEL` + `REG_WE`; **t_pd=0** |
| **CE / mailbox** | **hwsim ideal** | `MEM_DECODE_BREADBOARD` — 138×2 + glue comb |
| **Micro-phases, CW, flags, branches** | **[plover_vm](../plover_vm/)** | 10b Flash CW, `REG_WE`, `Y_OE`, CMP/BEQ |
| **OSC / ÷2 / 2 MHz recurring** | **not hwsim** | Validate on **scope** at B3c bring-up |

## Quick start

```bash
python -m hwsim run --all
```

## Commands

| Command | Description |
|---------|-------------|
| `python -m hwsim validate <netlist.yaml>` | BOM/pin/net checks |
| `python -m hwsim run <test.yaml>` | Run one timing test |
| `python -m hwsim run --all` | All tests in `hw/tests/` (excludes `archive/`) |
| `python -m hwsim report <build_dir>` | Regenerate HTML from JSON artifacts |

Outputs: `build/hwsim/<test_name>/` — `waves.json`, `timing_report.json`, `report.html`, `wiring.svg`

## Tests — CPU gate (v1.0 breadboard)

| Test | Block | Focus |
|------|-------|-------|
| `cpld_gpr_decode_breadboard` | cpld_gpr_ctrl | REG_SEL from CW → q_a/q_b |
| `mem_decode_breadboard` | sram256_breadboard | 138×2 + glue CE / mailbox |
| `cpld_regfile_dual_read` | cpld_regfile | CPLD GPR dual-read timing |
| `monitor_poll` | sram256_breadboard | MMIO STATUS poll stub |
| `boot_handoff` | mem_decode_breadboard | Reset $FFFC + Run mode |

**Archived legacy tests:** `hw/tests/archive/tier0/` (`regfile_574`, `mem_decode`, `cpld_gpr_decode`).

**Software boot:** [boot-jmp-handoff.md](boot-jmp-handoff.md)

## Tests — ALU bringup

See prior ALU table — `alu8_full`, `alu_b3_*`, etc. unchanged.

## Parity

```bash
pytest tests/test_mem_decode_breadboard.py -q
python tools/verify_control_store.py
```
