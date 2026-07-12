"""Desk model: single-clock vs CPLD µstep dual-clock IPC / macros-per-second.

stdlib only. SYS clock fixed at 2 MHz; USTEP only reduces SYS-visible cycles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


F_SYS_HZ = 2_000_000


@dataclass(frozen=True)
class MacroTemplate:
    name: str
    """SYS phases in baseline Gi1 (shared CLK)."""
    baseline_sys_cycles: int
    """SYS-visible bus/ALU cycles required under ustep (minimum)."""
    ustep_sys_cycles: int
    """Internal CU steps on CLK_USTEP (informational; do not add to SYS count)."""
    ustep_internal_steps: int = 0


# Gi1-inspired templates (research estimates, not normative).
SCENARIOS: dict[str, MacroTemplate] = {
    "ADD": MacroTemplate("ADD", baseline_sys_cycles=3, ustep_sys_cycles=1, ustep_internal_steps=4),
    "CMP": MacroTemplate("CMP", baseline_sys_cycles=3, ustep_sys_cycles=1, ustep_internal_steps=4),
    "MEM_LD": MacroTemplate("MEM_LD", baseline_sys_cycles=2, ustep_sys_cycles=2, ustep_internal_steps=2),
    "MEM_ST": MacroTemplate("MEM_ST", baseline_sys_cycles=2, ustep_sys_cycles=2, ustep_internal_steps=2),
    "BEQ": MacroTemplate("BEQ", baseline_sys_cycles=3, ustep_sys_cycles=3, ustep_internal_steps=2),
    "JMP": MacroTemplate("JMP", baseline_sys_cycles=3, ustep_sys_cycles=2, ustep_internal_steps=3),
    "CALL": MacroTemplate("CALL", baseline_sys_cycles=8, ustep_sys_cycles=7, ustep_internal_steps=6),
    "RET": MacroTemplate("RET", baseline_sys_cycles=6, ustep_sys_cycles=6, ustep_internal_steps=4),
}


@dataclass(frozen=True)
class RunResult:
    label: str
    macros: int
    sys_cycles: int
    f_sys_hz: int
    macros_per_s: float
    ipc: float  # macros / sys_cycles


def sys_cycles_for_program(
    program: Iterable[str],
    *,
    ustep: bool,
    sync_latency_sys: int = 0,
) -> tuple[int, int]:
    """Return (macro_count, total_sys_cycles)."""
    total = 0
    n = 0
    for name in program:
        t = SCENARIOS[name]
        n += 1
        if ustep:
            # One sync tax per macro that issues at least one SYS op.
            tax = sync_latency_sys if t.ustep_sys_cycles > 0 else 0
            total += t.ustep_sys_cycles + tax
        else:
            total += t.baseline_sys_cycles
    return n, total


def evaluate(
    program: Iterable[str],
    *,
    ustep: bool,
    sync_latency_sys: int = 0,
    f_sys_hz: int = F_SYS_HZ,
    label: str = "",
) -> RunResult:
    prog = list(program)
    n, cycles = sys_cycles_for_program(
        prog, ustep=ustep, sync_latency_sys=sync_latency_sys
    )
    if cycles <= 0 or n <= 0:
        raise ValueError("empty program or zero cycles")
    macros_per_s = n * (f_sys_hz / cycles)
    ipc = n / cycles
    mode = "ustep" if ustep else "baseline"
    return RunResult(
        label=label or mode,
        macros=n,
        sys_cycles=cycles,
        f_sys_hz=f_sys_hz,
        macros_per_s=macros_per_s,
        ipc=ipc,
    )


def uplift_pct(baseline: RunResult, candidate: RunResult) -> float:
    if baseline.macros_per_s <= 0:
        return 0.0
    return 100.0 * (candidate.macros_per_s - baseline.macros_per_s) / baseline.macros_per_s


# Representative mixes for desk reporting.
MIX_ALU_HEAVY = ["ADD", "ADD", "CMP", "ADD", "ADD"]
MIX_MEM_HEAVY = ["MEM_LD", "ADD", "MEM_ST", "MEM_LD", "ADD"]
MIX_CONTROL = ["ADD", "BEQ", "JMP", "CALL", "RET", "ADD"]
MIX_BALANCED = [
    "ADD",
    "MEM_LD",
    "ADD",
    "CMP",
    "MEM_ST",
    "BEQ",
    "ADD",
    "JMP",
]


def report_line(r: RunResult) -> str:
    return (
        f"{r.label:28s}  macros={r.macros:3d}  sys={r.sys_cycles:4d}  "
        f"IPC={r.ipc:.3f}  rate={r.macros_per_s/1e6:.3f} M/s"
    )


def main() -> None:
    print(f"F_SYS = {F_SYS_HZ/1e6:.1f} MHz\n")
    for name, mix in [
        ("ADD×10", ["ADD"] * 10),
        ("MEM_LD×10", ["MEM_LD"] * 10),
        ("alu_heavy", MIX_ALU_HEAVY),
        ("mem_heavy", MIX_MEM_HEAVY),
        ("control", MIX_CONTROL),
        ("balanced", MIX_BALANCED),
    ]:
        base = evaluate(mix, ustep=False, label=f"{name}/baseline")
        u0 = evaluate(mix, ustep=True, sync_latency_sys=0, label=f"{name}/ustep sync0")
        u1 = evaluate(mix, ustep=True, sync_latency_sys=1, label=f"{name}/ustep sync1")
        print(report_line(base))
        print(report_line(u0), f"  uplift={uplift_pct(base, u0):+.1f}%")
        print(report_line(u1), f"  uplift={uplift_pct(base, u1):+.1f}%")
        print()


if __name__ == "__main__":
    main()
