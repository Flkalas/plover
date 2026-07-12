#!/usr/bin/env python3
"""PE1 desk IPC model vs Gi1 / FE2 (stdlib only).

IPC = macros_retired / SYS
PE1: IF|EX overlap; bubbles for mem / taken branch / stack / operand bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


F_SYS_HZ = 2_000_000

# Import FE2/Gi1 totals from sibling study when available; else mirror constants.
try:
    import sys
    from pathlib import Path

    _sib = Path(__file__).resolve().parents[1].parent / "primitive-one-clock" / "model"
    if str(_sib) not in sys.path:
        sys.path.insert(0, str(_sib))
    from cycle_model import OPS as FE_OPS  # type: ignore
except Exception:  # pragma: no cover
    FE_OPS = None


@dataclass(frozen=True)
class Pe1Cost:
    name: str
    retire: int = 1
    operand_extra: int = 0
    mem_stall: int = 0
    branch_bubble: int = 0  # applied when taken=True for branches
    stack_extra: int = 0
    is_branch: bool = False


PE1: dict[str, Pe1Cost] = {
    "ADD": Pe1Cost("ADD", operand_extra=1),
    "CMP": Pe1Cost("CMP", operand_extra=1),
    "LDA": Pe1Cost("LDA", operand_extra=1, mem_stall=1),
    "STA": Pe1Cost("STA", operand_extra=1, mem_stall=1),
    "BEQ": Pe1Cost("BEQ", operand_extra=2, is_branch=True, branch_bubble=1),
    "JMP": Pe1Cost("JMP", operand_extra=2, is_branch=True, branch_bubble=1),
    "CALL": Pe1Cost(
        "CALL", operand_extra=2, is_branch=True, branch_bubble=1, stack_extra=2
    ),
    "RET": Pe1Cost("RET", is_branch=True, branch_bubble=1, stack_extra=2),
}


def pe1_sys(name: str, *, taken: bool = True, alu_stream: bool = False) -> int:
    """SYS for one macro. alu_stream: hide operand_extra (imm fetched in prior shadow)."""
    c = PE1[name]
    opx = 0 if alu_stream and name in ("ADD", "CMP") else c.operand_extra
    br = c.branch_bubble if (c.is_branch and taken) else 0
    if name == "BEQ" and not taken:
        br = 0
    return c.retire + opx + c.mem_stall + br + c.stack_extra


def gi1_sys(name: str) -> int:
    if FE_OPS is None:
        fallback = {
            "ADD": 5,
            "CMP": 5,
            "LDA": 4,
            "STA": 4,
            "BEQ": 5,
            "JMP": 4,
            "CALL": 8,
            "RET": 5,
        }
        return fallback[name]
    return FE_OPS[name].gi1_total


def fe2_sys(name: str) -> int:
    if FE_OPS is None:
        fallback = {
            "ADD": 3,
            "CMP": 3,
            "LDA": 3,
            "STA": 3,
            "BEQ": 4,
            "JMP": 4,
            "CALL": 6,
            "RET": 3,
        }
        return fallback[name]
    return FE_OPS[name].fe2_total


@dataclass(frozen=True)
class RunResult:
    label: str
    macros: int
    sys_cycles: int
    macros_per_s: float
    ipc: float


def evaluate(
    program: Iterable[tuple[str, bool] | str],
    *,
    mode: str,
    alu_stream: bool = False,
    f_sys_hz: int = F_SYS_HZ,
) -> RunResult:
    """program entries: name or (name, taken)."""
    n = 0
    cycles = 0
    for item in program:
        if isinstance(item, tuple):
            name, taken = item
        else:
            name, taken = item, True
        n += 1
        if mode == "gi1":
            cycles += gi1_sys(name)
        elif mode == "fe2":
            cycles += fe2_sys(name)
        elif mode == "pe1":
            cycles += pe1_sys(name, taken=taken, alu_stream=alu_stream)
        else:
            raise ValueError(mode)
    if n <= 0 or cycles <= 0:
        raise ValueError("empty")
    return RunResult(
        label=mode,
        macros=n,
        sys_cycles=cycles,
        macros_per_s=n * (f_sys_hz / cycles),
        ipc=n / cycles,
    )


def uplift_pct(base: RunResult, cand: RunResult) -> float:
    if base.macros_per_s <= 0:
        return 0.0
    return 100.0 * (cand.macros_per_s - base.macros_per_s) / base.macros_per_s


MIX_ALU = ["ADD"] * 20
MIX_BALANCED = [
    "ADD",
    "LDA",
    "ADD",
    "CMP",
    "STA",
    ("BEQ", True),
    "ADD",
    "JMP",
]
MIX_BRANCHY = [("BEQ", True), "JMP", ("BEQ", False), "ADD"] * 3


def main() -> None:
    print(f"F_SYS = {F_SYS_HZ / 1e6:.1f} MHz  (PE1 research)\n")
    for title, mix, pe1_kwargs in [
        ("ALU×20 (cold operand)", MIX_ALU, {}),
        ("ALU×20 (stream, imm shadowed)", MIX_ALU, {"alu_stream": True}),
        ("balanced", MIX_BALANCED, {}),
        ("branchy", MIX_BRANCHY, {}),
    ]:
        print(f"=== {title} ===")
        g = evaluate(mix, mode="gi1")
        f2 = evaluate(mix, mode="fe2")
        p = evaluate(mix, mode="pe1", **pe1_kwargs)
        for r, tag in ((g, "gi1"), (f2, "fe2"), (p, "pe1")):
            u = ""
            if tag != "gi1":
                u = f"  uplift_vs_gi1={uplift_pct(g, r):+.1f}%"
            print(
                f"  {tag:4s}  macros={r.macros:3d}  sys={r.sys_cycles:4d}  "
                f"IPC={r.ipc:.3f}  rate={r.macros_per_s / 1e6:.3f} M/s{u}"
            )
        print()


if __name__ == "__main__":
    main()
