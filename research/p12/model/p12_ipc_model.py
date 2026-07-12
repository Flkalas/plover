#!/usr/bin/env python3
"""P12 desk IPC model vs Gi1 / FE2 / PE1 (stdlib only).

P12 = PE1 pipe costs + optional FE2-style stretch + fallback_fe2.
IPC = macros_retired / SYS
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


F_SYS_HZ = 2_000_000

try:
    import sys
    from pathlib import Path

    _root = Path(__file__).resolve().parents[1].parent
    for _sib in (
        _root / "primitive-one-clock" / "model",
        _root / "pe1" / "model",
    ):
        if str(_sib) not in sys.path:
            sys.path.insert(0, str(_sib))
    from cycle_model import OPS as FE_OPS  # type: ignore
    from pe1_ipc_model import (  # type: ignore
        pe1_sys as _pe1_sys,
        gi1_sys as _gi1_sys,
        fe2_sys as _fe2_sys,
    )
except Exception:  # pragma: no cover
    FE_OPS = None
    _pe1_sys = None
    _gi1_sys = None
    _fe2_sys = None


# First FE2-style stretch deltas (lab failed once).
STRETCH_EXTRA: dict[str, int] = {
    "LDA": 1,
    "STA": 1,
    "BEQ": 1,  # when taken
    "CALL": 1,
    "RET": 1,
}


def gi1_sys(name: str) -> int:
    if _gi1_sys is not None:
        return _gi1_sys(name)
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


def fe2_sys(name: str) -> int:
    if _fe2_sys is not None:
        return _fe2_sys(name)
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


def pe1_sys(name: str, *, taken: bool = True, alu_stream: bool = False) -> int:
    if _pe1_sys is not None:
        return _pe1_sys(name, taken=taken, alu_stream=alu_stream)
    # Mirror pe1_ipc_model if import failed
    base = {
        "ADD": (1, 1, 0, 0, 0, False),
        "CMP": (1, 1, 0, 0, 0, False),
        "LDA": (1, 1, 1, 0, 0, False),
        "STA": (1, 1, 1, 0, 0, False),
        "BEQ": (1, 2, 0, 1, 0, True),
        "JMP": (1, 2, 0, 1, 0, True),
        "CALL": (1, 2, 0, 1, 2, True),
        "RET": (1, 0, 0, 1, 2, True),
    }
    retire, opx, mem, br, stack, is_br = base[name]
    if alu_stream and name in ("ADD", "CMP"):
        opx = 0
    bubble = br if (is_br and taken) else 0
    if name == "BEQ" and not taken:
        bubble = 0
    return retire + opx + mem + bubble + stack


def p12_sys(
    name: str,
    *,
    taken: bool = True,
    alu_stream: bool = False,
    stretch: bool = False,
) -> int:
    """Optimistic P12 == PE1; stretch adds FE2-style first +1 on select ops."""
    n = pe1_sys(name, taken=taken, alu_stream=alu_stream)
    if not stretch:
        return n
    extra = STRETCH_EXTRA.get(name, 0)
    if name == "BEQ" and not taken:
        extra = 0
    return n + extra


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
        elif mode == "fe2" or mode == "fallback_fe2":
            cycles += fe2_sys(name)
        elif mode == "pe1" or mode == "p12":
            cycles += p12_sys(name, taken=taken, alu_stream=alu_stream, stretch=False)
        elif mode == "p12_stretch":
            cycles += p12_sys(name, taken=taken, alu_stream=alu_stream, stretch=True)
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
    print(f"F_SYS = {F_SYS_HZ / 1e6:.1f} MHz  (P12 research)\n")
    modes = ("gi1", "fe2", "pe1", "p12", "p12_stretch", "fallback_fe2")
    for title, mix, kwargs in [
        ("ALU×20 (cold operand)", MIX_ALU, {}),
        ("ALU×20 (stream, imm shadowed)", MIX_ALU, {"alu_stream": True}),
        ("balanced", MIX_BALANCED, {}),
        ("branchy", MIX_BRANCHY, {}),
    ]:
        print(f"=== {title} ===")
        g = evaluate(mix, mode="gi1")
        for mode in modes:
            r = evaluate(mix, mode=mode, **kwargs)
            u = ""
            if mode != "gi1":
                u = f"  uplift_vs_gi1={uplift_pct(g, r):+.1f}%"
            print(
                f"  {mode:13s}  macros={r.macros:3d}  sys={r.sys_cycles:4d}  "
                f"IPC={r.ipc:.3f}  rate={r.macros_per_s / 1e6:.3f} M/s{u}"
            )
        print()


if __name__ == "__main__":
    main()
