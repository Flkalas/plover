# ATF1504 FSM fit study (research sandbox)

**Status:** Research only — does **not** change v1.0 normative sources.

| Tier | Path | Role |
|------|------|------|
| **Frozen** | `cpld_fsm/hdl/`, `reference/**`, `plover-whitepaper.md` | v1.0 production baseline (read-only for this study) |
| **Research** | `cpld_fsm/fit-study/` | Variant pin/MC/timing analysis, PLD forks, report |

## Purpose

Explore how to achieve **full logical I/O parity** (42-pin budget) and **MC headroom** on ATF1504AS-10JU44 while keeping the **12-DIP ALU** datapath. Current production Tier C fits **32/32** user I/O with **trimmed** `q_a3..7` / `q_b3..7` export.

## Index

| Path | Content |
|------|---------|
| [REPORT.md](REPORT.md) | Baseline fit study (A1, D5a) |
| [REPORT-e1-gpr-eeprom.md](REPORT-e1-gpr-eeprom.md) | **E1** GPR-in-CPLD + EEPROM FSM report |
| [pin-budget-variants.md](pin-budget-variants.md) | A1–D5 pin math |
| [pin-budget-e1.md](pin-budget-e1.md) | E1 pin subcases |
| [tfr-isa-variants.md](tfr-isa-variants.md) | TFR encoding alternatives (fit-study) |
| [timing-clock-table.md](timing-clock-table.md) | P0–P6 paths and `f_clk` derivation |
| [fit-logs/](fit-logs/) | Baseline MC notes, variant synthesis logs |
| [variants/](variants/) | Per-variant PLD forks (not production bitstream) |
| [sim/](sim/) | EEPROM CW store, external 574 GPR models |
| [scripts/](scripts/) | `gen_eeprom_cw.py` and variant build helpers |
| [tests/](tests/) | Research-only pytest (v1.0 golden unchanged) |

## Apply (out of scope)

Adopting a variant into v1.0 requires a **separate plan** and edits to `reference/**` + `cpld_fsm/hdl/`. This folder records options only.
