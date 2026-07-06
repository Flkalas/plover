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

## Current fit (Tier A — 2026-07-06)

**Exported to package** (`pin =` in PLD):

| Signal | cyclesim net | Notes |
|--------|--------------|-------|
| `reg_we` | `net_reg_we` | |
| `q_a0..7` | `net_a0..7` | R0 async read (hardware; sim uses GPR block) |
| `q_b0..5` | `net_b0..5` | R1 low 6 bits |
| `q_b6`, `q_b7` | — | **Internal** (I/O budget); strap at ALU bring-up |

**Internal** (equations live; no package pin in this fit):

| Signal | cyclesim net | Breadboard |
|--------|--------------|------------|
| `mem_rd`, `mem_wr`, `y_oe` | `net_mem_*`, `net_y_oe` | Tier B / glue (138 tree) |
| `flg_we` | `net_flg_we` | |
| `pc_load_en` | `net_pc_load_en` | BEQ path — needs `flg_z` + spare I/O |
| `flg_z` | (input) | **Not pinned** in Tier A fit — add I/O or drop one export |
| `cin`, `bctrl0..3`, `lgc0..3`, `s0`, `s1` | ALU nets | `bctrl1←0`, `bctrl3←2`; lgc/s tie GND |
| `w_sel0/1` | `net_w_sel*` | Inside CPLD by design |

Run `python gen_pin_lock.py` after each fit for the authoritative pin → signal table.

## I/O math

| Tier | Inputs | Outputs | Total | Status |
|------|--------|---------|-------|--------|
| A (current) | 17 (fitter-placed) | 16 | 32/32 | **Fits** |
| A + `pc_load_en` + `flg_z` | 15 locked | 18 | 33 | Does not fit |
| B (+ JTAG as GPIO strobes) | 15 | 22 | 37 | Needs larger part or latch |

## Tier C — external CW latch (normative SoC)

Normative spec: [control-word-latch.md](../../reference/hardware/control-word-latch.md).

| CPLD export | Width | Role |
|-------------|------:|------|
| `cw_data[7:0]` | 8 | Muxed CW load data |
| `cw_le` | 1 | 574 clock (both CW_LO/CW_HI) |
| `cw_bank` | 1 | 0=CW_LO, 1=CW_HI |

**Externalized via 574×2** (not CPLD pads): `mem_rd`, `mem_wr`, `y_oe`, `flg_we`, `pc_load_en`, `cin`, `bctrl0..3`, `lgc0..3`, `s0`, `s1`.

| Tier | Control bundle | CPLD CW pins | vs 14 dedicated strobes |
|------|----------------|-------------:|------------------------:|
| A | Internal / strap | 0 | — |
| C | CW latch | **10** | saves ~4 net pins on CPLD |

PLD/CW mux implementation is **not** in current bitstream — documentation only until follow-up fit.

## JTAG vs run mode

- **Program:** ISP on pins 7/13/32/38; do not depend on strobes on those pads.
- **Run:** Tier B may map `mem_rd`/`mem_wr`/`y_oe` onto ex-JTAG pads after disconnecting the programmer.
