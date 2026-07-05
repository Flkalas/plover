# Plover CPLD FSM — WinCUPL build (ATF1504AS)

Target: **ATF1504AS-10JU44** · idx5 GPR + phase FSM (~38 MC / 64 max).

## Sources

| File | Role |
|------|------|
| [`system_ctrl.pld`](system_ctrl.pld) | CUPL top (GPR, phase, xfer, branch) |
| [`ctrl_lut.inc`](ctrl_lut.inc) | **Generated** idx5 LUT equations |
| [`gen_ctrl_lut.py`](gen_ctrl_lut.py) | Codegen from `fsm_table.py` |
| [`build-wincupl.ps1`](build-wincupl.ps1) | CUPL + FIT1504 CLI (optional) |

## Install WinCUPL

1. Download [WinCUPL](https://www.microchip.com/en-us/products/fpgas-and-plds/spld-cplds/pld-design-resources) (Microchip SPLD/CPLD design resources).
2. Set environment variables:
   - `WINCUPL_DIR` → install root (e.g. `C:\WinCUPL`)
   - `FITTERDIR` → `%WINCUPL_DIR%\Fitters` (**required** for JED; silent failure if missing)
3. Use a **short project path** (fitter path limit ~128 characters).

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

On success: `system_ctrl.jed` in this folder. Check fitter log for **MC ≤ 64**.

## Pin lock

After fit, export pin report → update:

- [`system_ctrl.pin`](system_ctrl.pin)
- [`../netlist/cpld_system_ctrl.yaml`](../netlist/cpld_system_ctrl.yaml)

Locked in PLD: **clk** pin 43 (GCLK1). JTAG 7/13/32/38 reserved by ISP device type.

## Verification (no silicon)

```powershell
pytest simulators/cyclesim/tests/test_fsm_idx5.py simulators/cyclesim/tests/test_alu8.py
pytest cpld_fsm/hdl/tests/test_gen_ctrl_lut.py
```

## Flash (follow-up)

[`../tools/wiring-flash.md`](../tools/wiring-flash.md) · JED → SVF (ATMISP) · [`../tools/jtag-probe.ps1`](../tools/jtag-probe.ps1)
