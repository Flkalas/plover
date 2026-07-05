# Plover CPLD FSM — VHDL build (ProChip Designer)

Target: **ATF1504AS-10JU44** · idx5 GPR + phase FSM (~38 MC / 64 max).

## Sources

| File | Role |
|------|------|
| `system_ctrl.vhd` | Top |
| `gpr_3fixed.vhd` | R0–R2, async `q_a`/`q_b` |
| `phase_sequencer.vhd` | 2-bit phase + `PHASE_COUNT` |
| `ctrl_lut.vhd` | **Generated** idx5 → strobes + ALU |
| `xfer_mux.vhd` | TFR `0x10`–`0x15` internal read |
| `branch_unit.vhd` | BEQ `FLG_Z` gate |
| `gen_ctrl_lut.py` | Codegen from `simulators/cyclesim/data/fsm_table.py` |

## Codegen

```powershell
cd <repo-root>
python cpld_fsm/hdl/gen_ctrl_lut.py
```

Re-run after any `fsm_table.py` change. Gate: `pytest simulators/cyclesim/tests/test_fsm_idx5.py`.

## ProChip Designer

1. Download [ProChip Designer](https://www.microchip.com/en-us/products/fpgas-and-plds/cpld/spld-cplds/prochip-designer) (Atmel WinCUPL/ProChip lineage).
2. Device: **ATF1504AS**, package **PLCC-44**, speed **-10**, **JTAG ISP on**.
3. Add all `.vhd` files; top = `system_ctrl`.
4. Pin lock: `system_ctrl.pin` (JTAG TDI/TMS/TCK/TDO + CLK on GCLK1).
5. **Fit** → MC ≤ **64** (target ~38). Save fitter log into `fit_report.txt`.
6. **Generate JED** → `system_ctrl.jed` (replaces erased stub from `gen_jed_stub.py`).

## Pin / netlist sync

After fit, export pins to:

- `system_ctrl.pin`
- `../netlist/cpld_system_ctrl.yaml`

## Cyclesim cross-check

| Check | Command |
|-------|---------|
| idx5 table | `pytest simulators/cyclesim/tests/test_fsm_idx5.py` |
| ALU macro ops | `pytest simulators/cyclesim/tests/test_alu8.py` |
| Codegen golden | `pytest cpld_fsm/hdl/tests/test_gen_ctrl_lut.py` |

## JTAG (post-JED)

Flash wiring: `../tools/wiring-flash.md` · probe: `../tools/jtag-probe.ps1` (ID `0x0150403f`).
