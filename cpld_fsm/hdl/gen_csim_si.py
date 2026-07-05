#!/usr/bin/env python3
"""Generate WinCUPL csim vector file (.si) from fsm_table.py."""

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
    CSIM_INPUT_ORDER,
    FSM_OUTPUT_SIGNALS,
    find_inactive_idx5_lut,
    format_csim_vector,
)
from sim_fsm_eval import load_ctrl_lut_equations  # noqa: E402
from simulators.cyclesim.data.fsm_table import FSM_ROWS  # noqa: E402
from simulators.cyclesim.data.isa import TFR_OPS  # noqa: E402

LUT = Path(__file__).resolve().parent / "ctrl_lut.inc"

OUT = Path(__file__).resolve().parent / "system_ctrl_gen.si"


def emit_si() -> str:
    in_list = ", ".join(CSIM_INPUT_ORDER)
    out_list = ", ".join(FSM_OUTPUT_SIGNALS)
    lines = [
        "Name      system_ctrl;",
        "Partno    00;",
        "Date      07/06/2026;",
        "Rev       01;",
        "Designer  Plover;",
        "Company   Plover;",
        "Assembly  None;",
        "Location  None;",
        "Device    f1504ispplcc44;",
        "",
        f"ORDER: {in_list}, %2,",
        f"       {out_list};",
        "",
        "VECTORS:",
    ]
    for row in FSM_ROWS:
        lines.append(
            format_csim_vector(
                row.opcode,
                row.phase,
                comment=f"idx5={row.idx5:02d} op=0x{row.opcode:02X} ph={row.phase}",
            )
        )
    # Spot-check: inactive idx5 slot with all LUT outputs low
    inactive = find_inactive_idx5_lut(load_ctrl_lut_equations(LUT))
    op = (inactive >> 2) & 0x1F
    ph = inactive & 3
    lines.append(format_csim_vector(op, ph, comment=f"idx5={inactive:02d} inactive"))
    # TFR opcodes: outside idx5 LUT — all LUT outputs must stay low
    for tfr_op in sorted(TFR_OPS):
        lines.append(
            format_csim_vector(
                tfr_op,
                0,
                comment=f"TFR 0x{tfr_op:02X} comb (LUT inactive)",
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT.write_text(emit_si(), encoding="utf-8")
    print(f"Wrote {OUT} ({len(FSM_ROWS)} active rows + 1 inactive + {len(TFR_OPS)} TFR vectors)")


if __name__ == "__main__":
    main()
