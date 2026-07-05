#!/usr/bin/env python3
"""Generate combinational ctrl_lut_csim.pld + .si for WinCUPL csim (LUT-only)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HDL = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HDL) not in sys.path:
    sys.path.insert(0, str(HDL))

from fsm_golden import (  # noqa: E402
    FSM_OUTPUT_SIGNALS,
    find_inactive_idx5_lut,
    format_csim_vector,
)
from sim_fsm_eval import load_ctrl_lut_equations  # noqa: E402
from simulators.cyclesim.data.fsm_table import FSM_ROWS  # noqa: E402
from simulators.cyclesim.data.isa import TFR_OPS  # noqa: E402

LUT = HDL / "ctrl_lut.inc"
PLD = HDL / "ctrl_lut_csim.pld"
SI = HDL / "ctrl_lut_csim.si"

CSIM_INPUTS = ("opc0", "opc1", "opc2", "opc3", "opc4", "ph0", "ph1")

INPUT_PINS = {"opc0": 4, "opc1": 5, "opc2": 6, "opc3": 8, "opc4": 9, "ph0": 24, "ph1": 25}


def emit_pld() -> str:
    lut_body = LUT.read_text(encoding="utf-8").strip()
    in_pins = "\n".join(f"PIN {pin:2d} = {sig};" for sig, pin in INPUT_PINS.items())
    return f"""Name ctrl_lut_csim;
Partno 00;
Date 07/06/2026;
Revision 01;
Designer Plover;
Company Plover;
Assembly None;
Location None;
Device f1504ispplcc44;

/* Combinational idx5 LUT only - ph0/ph1 are inputs for csim (not registered). */

{in_pins}

{lut_body}
"""


def emit_si() -> str:
    in_list = ", ".join(CSIM_INPUTS)
    out_list = ", ".join(FSM_OUTPUT_SIGNALS)
    lines = [
        "Name      ctrl_lut_csim;",
        "Partno    00;",
        "Date      07/06/2026;",
        "Rev       01;",
        "Designer  Plover;",
        "Company   Plover;",
        "Assembly  None;",
        "Location  None;",
        "Device    f1504ispplcc44;",
        "",
        f"ORDER: {in_list}, %1, {out_list};",
        "",
        "VECTORS:",
    ]
    for row in FSM_ROWS:
        lines.append(
            format_csim_vector(
                row.opcode,
                row.phase,
                comment=f"idx5={row.idx5:02d}",
                input_order=CSIM_INPUTS,
            )
        )
    inactive = find_inactive_idx5_lut(load_ctrl_lut_equations(LUT))
    op = (inactive >> 2) & 0x1F
    ph = inactive & 3
    lines.append(format_csim_vector(op, ph, comment="inactive", input_order=CSIM_INPUTS))
    for tfr_op in sorted(TFR_OPS):
        lines.append(
            format_csim_vector(
                tfr_op, 0, comment=f"TFR 0x{tfr_op:02X}", input_order=CSIM_INPUTS
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not LUT.is_file():
        raise SystemExit(f"missing {LUT} — run gen_ctrl_lut.py first")
    PLD.write_text(emit_pld(), encoding="utf-8")
    SI.write_text(emit_si(), encoding="utf-8")
    print(f"Wrote {PLD.name}, {SI.name} ({len(FSM_ROWS)} rows + inactive + {len(TFR_OPS)} TFR)")


if __name__ == "__main__":
    main()
