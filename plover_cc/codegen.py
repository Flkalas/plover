"""Subset-C code generator to Plover asm (S5)."""

from __future__ import annotations

from plover_cc.parse import Program


def program_to_asm(prog: Program) -> str:
    # Normative ADD: R2 <- R0+imm; MOV 2 copies R2 -> R0 for PL-DOS spawn display.
    v = prog.return_value & 0xFF
    return "\n".join(
        [
            "        .ORG 0",
            f"        ADD {v}",
            "        MOV 2",
            "        HALT",
            "",
        ]
    )

