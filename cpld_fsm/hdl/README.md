# Plover CPLD FSM — WinCUPL build (ATF1504AS)

Target: **ATF1504AS-10JU44** · idx5 GPR + phase FSM (64 MC device).

**Truth cascade:** [plover-whitepaper.md](../../plover-whitepaper.md) §6 → `reference/**` → `simulators/cyclesim/data/{isa,fsm_table}.py` → this folder. TFR comb (`tfr_valid`) is hand-written in `system_ctrl.pld`; idx5 LUT is codegen from `fsm_table.py`.

## Sources

| File | Role |
|------|------|
| [`system_ctrl.pld`](system_ctrl.pld) | CUPL top (GPR, phase, xfer, branch) |
| [`ctrl_lut.inc`](ctrl_lut.inc) | **Generated** idx5 LUT equations |
| [`gen_ctrl_lut.py`](gen_ctrl_lut.py) | Codegen from `fsm_table.py` |
| [`gen_csim_si.py`](gen_csim_si.py) | WinCUPL csim vector file (optional smoke) |
| [`fsm_golden.py`](fsm_golden.py) | Golden helpers shared by codegen and tests |
| [`sim_fsm_eval.py`](sim_fsm_eval.py) | Evaluate `ctrl_lut.inc` idx5 equations |
| [`build-wincupl.ps1`](build-wincupl.ps1) | CUPL + FIT1504 CLI (optional) |

## Install WinCUPL

1. Download [WinCUPL II v1.1.0](https://www.microchip.com/en-us/development-tool/WINCUPL) ZIP (browser).
2. Unpack without running Setup.exe:

```powershell
cd cpld_fsm/tools
./install-wincupl.ps1
```

Uses **innounp** to extract `Setup.exe` inside the ZIP — no installer, no reboot.  
Output: `cpld_fsm/tools/wincupl-ii/` (auto-detected by `build-wincupl.ps1`).

Use a **short project path** (fitter path limit ~128 characters).

Device in PLD header: **`f1504ispplcc44`** (JTAG ISP for FT232H).

## Codegen

```powershell
cd <repo-root>
python cpld_fsm/hdl/gen_ctrl_lut.py
```

Writes `ctrl_lut.inc` and `system_ctrl_gen.pld` (merged). Re-run after any `fsm_table.py` change.

## Build JED

### GUI

1. Open `system_ctrl_gen.pld` in WinCUPL (run codegen first).
2. **Run → Device Dependent Compile** (F9).
3. Confirm `system_ctrl_gen.jed` (or copy to `system_ctrl.jed`).

### CLI

```powershell
cd cpld_fsm/hdl
./build-wincupl.ps1
```

On success: `system_ctrl.jed` in this folder. Check fitter log for **Design FITS**.

## Pin lock

After fit, export pin report → update:

- [`system_ctrl.pin`](system_ctrl.pin)
- [`../netlist/cpld_system_ctrl.yaml`](../netlist/cpld_system_ctrl.yaml)

Locked in PLD: **clk** pin 43 (GCLK1). JTAG 7/13/32/38 reserved by ISP device type.

## Verification (no silicon)

Golden table: `simulators/cyclesim/data/fsm_table.py` (20 active idx5 rows; TFR comb outside LUT).

| Layer | Test file | What it checks |
|-------|-----------|----------------|
| LUT text | `tests/test_gen_ctrl_lut.py` | `ctrl_lut.inc` contains correct idx5 terms |
| LUT eval | `tests/test_csim_fsm_table.py` | Python evaluator vs golden table |
| cyclesim FSM | `tests/test_csim_fsm_table.py` | `CtrlLookup` vs golden table |
| Merged strobes | `tests/test_merged_strobe_parity.py` | LUT → PLD merge → `CtrlLookup` |
| CPU macros | `simulators/cyclesim/tests/test_cpu_m3b.py` | ADD/CMP ph1 REG_WE, TFR, fib, fetch, branch, MMIO |

Full parity matrix: [simulators/README.md](../../simulators/README.md#parity-matrix-functional).

**Note:** CUPL compiler `.sim` equations are optimized and may differ from the idx5 LUT; parity tests use **`ctrl_lut.inc`**, not `.sim`. CI uses Python LUT eval only (no WinCUPL `csim.exe`).

```powershell
pytest simulators/cyclesim/tests cpld_fsm/hdl/tests -q
```

## Flash (follow-up)

[`../tools/wiring-flash.md`](../tools/wiring-flash.md) · JED → SVF (ATMISP) · [`../tools/jtag-probe.ps1`](../tools/jtag-probe.ps1)
