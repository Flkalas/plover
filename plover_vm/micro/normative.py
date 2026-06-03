"""Macro-level effects matching micro-phase + hwsim/cyclesim datapath."""

from __future__ import annotations

from plover_vm.alu import alu8


def apply_add(regs: list[int], imm: int) -> tuple[list[int], bool, bool]:
    """ADD: optional imm→R1, R2 ← R0+R1 (micro ph0–2 / cyclesim)."""
    r = list(regs)
    if imm:
        r[1] = imm & 0xFF
    res = alu8(r[0], r[1], 1)
    r[2] = res.y & 0xFF
    return r, res.zero, res.cout


def apply_cmp_flags(regs: list[int], imm: int) -> tuple[bool, bool]:
    res = alu8(regs[0], imm & 0xFF, 2)
    return res.zero, res.cout


def apply_beq_compare(regs: list[int], imm: int) -> tuple[bool, bool]:
    return apply_cmp_flags(regs, imm)
