"""Subset-C code generator to Plover asm (S5)."""

from __future__ import annotations

from plover_cc.parse import Program


def program_to_asm(prog: Program) -> str:
    # R0 starts at 0 on reset; use ADD imm to set return value.
    v = prog.return_value & 0xFF
    return "\n".join(
        [
            "        .ORG 0",
            f"        ADD {v}",
            "        HALT",
            "",
        ]
    )

