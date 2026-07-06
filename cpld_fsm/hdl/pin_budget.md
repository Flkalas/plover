# CPLD package pin budget (ATF1504 PLCC-44)

Normative port list: [cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) §2.  
Simulator merged strobes: `cpld_fsm/hdl/fsm_golden.py` → `CYCLESIM_NET_MAP`.

## Device limit

| Resource | Count |
|----------|------:|
| User I/O (fitter) | **32** |
| JTAG dedicated (7/13/32/38) | 4 (GPIO after ISP burn) |
| GCLK / clk | pin 43 |

## PLD export method (WinCUPL)

1. Declare package outputs with **`pin = signal;`** (no pad number) in `system_ctrl.pld`.
2. Set **`PROPERTY ATMEL {PREASSIGN = OFF};`** so the fitter can place GPR FF on I/O macrocells.
3. Run `build-wincupl.ps1` → confirm **Design fits**.
4. Run `python gen_pin_lock.py` → refresh `system_ctrl.pin`.
5. Wire breadboard to **fitter pins** in `system_ctrl_gen.fit` § “Pin/Node Placement”, not pre-fit YAML guesses.

`PIN nn = signal` on outputs with `PREASSIGN = KEEP` often causes **Grouping fail** (register bank vs pad lock).  
Numbered locks on **inputs only** + buried outputs → fit passes but **0–1 package outputs** (internal strobes only).

## Current fit (Tier C — 2026-07-06)

**Design fits** at **32/32 user I/O** with CW bus + fitter-first GPR trim.

**Exported to package** (`pin =` in PLD; pins from `system_ctrl.pin`):

| Signal | cyclesim net | Pin(s) | Notes |
|--------|--------------|--------|-------|
| `reg_we` | `net_reg_we` | 14 | |
| `cw_data[7:0]` | (Tier C latch load) | 16–21, 37, 40, 20 | Muxed CW load data |
| `cw_le` | `cw_le` | 39 | 574 clock |
| `cw_bank` | `cw_bank` | 41 | 0=CW_LO, 1=CW_HI |
| `q_a0..2` | `net_a0..2` | 29, 31, 28 | R0 async read (low 3 bits) |
| `q_b0..2` | `net_b0..2` | 26, 27, 25 | R1 async read (low 3 bits) |

**Internal** (equations live; no package pin in this fit):

| Signal | cyclesim net | Breadboard |
|--------|--------------|------------|
| `q_a3..7`, `q_b3..7` | upper GPR read bits | Strap or buffer from latched GPR during bring-up |
| `mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, `cin`, `bctrl*`, `lgc*`, `s0`, `s1` | via **CW latch** | External 574×2 per [control-word-latch.md](../../reference/hardware/control-word-latch.md) |

**Inputs** (fitter-placed; see `system_ctrl.pin`): `OPC[4:0]`, `d_in[7:0]`, `FLG_Z` (pin 36), `CLK` (43).

Run `python gen_pin_lock.py` after each fit for the authoritative pin → signal table.

## I/O math

| Tier | Inputs | Outputs | Total | Status |
|------|--------|---------|-------|--------|
| A (prior) | 17 | 16 | 32/32 | Fits (no CW bus) |
| **C (current)** | 15 | 17 | **32/32** | **Fits** — CW bus 10 + `reg_we` + 6 GPR bits |
| C + full `q_a`/`q_b` | 15 | 27 | 42 | Does not fit |

## Tier C — external CW latch (normative SoC)

Normative spec: [control-word-latch.md](../../reference/hardware/control-word-latch.md).

| CPLD export | Width | Role |
|-------------|------:|------|
| `cw_data[7:0]` | 8 | Muxed CW load data |
| `cw_le` | 1 | 574 clock (both CW_LO/CW_HI) |
| `cw_bank` | 1 | 0=CW_LO, 1=CW_HI |

**Externalized via 574×2** (not CPLD pads): `mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, `cin`, `bctrl0..3`, `lgc0..3`, `s0`, `s1`.

**Implemented** in `system_ctrl.pld` (2026-07-06): CW pack/mux, phase-edge 2-pulse load sequencer, fitter-first `q_a0..2` / `q_b0..2` export.

## JTAG vs run mode

- **Program:** ISP on pins 7/13/32/38; do not depend on strobes on those pads.
- **Run:** Tier B may map `mem_rd`/`mem_wr`/`y_oe` onto ex-JTAG pads after disconnecting the programmer.
