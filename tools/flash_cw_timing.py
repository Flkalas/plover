#!/usr/bin/env python3
"""End-to-end Flash CW execute-phase timing budget @ 2 MHz (250 ns half-period).

Loads datasheet delays from hw/timing/*.yaml. Compares serial vs pipelined schedules.
Research only — not normative bring-up.

Usage:
  python tools/flash_cw_timing.py
  python tools/flash_cw_timing.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hwsim.netlist import delay_ns, load_timing  # noqa: E402

EXEC_HALF_NS = 250
DELAY_DECODE_SAVED = 15
DELAY_SUB_WITH_DECODE = 151
DELAY_CW16_DIRECT = DELAY_SUB_WITH_DECODE - DELAY_DECODE_SAVED
DELAY_CPLD_REG_PENALTY = 5
DELAY_EXT_CTRL_PENALTY = 8

ARCH_BASELINE_FSM = "baseline_fsm"
ARCH_FLASH_CW10 = "flash_cw10_decode"
ARCH_FLASH_CW16 = "flash_cw16_direct"
ARCH_COUNTER_TEMPLATE = "counter_template"


@dataclass(frozen=True)
class TimingConstants:
    mux_157_ns: int
    flash_acc_ns: int
    latch_setup_ns: int
    latch_q_ns: int
    alu_sub_decode_ns: int
    alu_sub_direct_ns: int
    phase_161_q_ns: int


@dataclass(frozen=True)
class ArchTimingBudget:
    arch: str
    delay_alu_ns: int
    delay_fetch_ns: int
    delay_execute_ns: int
    serial_total_ns: int
    pipelined_fetch_slack_ns: int
    pipelined_execute_slack_ns: int
    pipelined_ok: bool
    serial_ok: bool
    schedule: str
    bottleneck: str


def load_constants(mode: str = "max") -> TimingConstants:
    timing = load_timing(ROOT, mode)
    return TimingConstants(
        mux_157_ns=delay_ns(timing, "74HC157", "t_pd", default=18),
        flash_acc_ns=delay_ns(timing, "ROM_CTRL", "t_pd", default=70),
        latch_setup_ns=delay_ns(timing, "74HC574", "t_setup", default=8),
        latch_q_ns=delay_ns(timing, "74HC574", "t_pd_q", default=23),
        alu_sub_decode_ns=delay_ns(timing, "ALU_CMP_SUB", "t_pd", default=151),
        alu_sub_direct_ns=DELAY_CW16_DIRECT,
        phase_161_q_ns=delay_ns(timing, "74HC161", "t_clk_to_q", default=25),
    )


def flash_fetch_ns(c: TimingConstants, *, extra_mux_ns: int = 0) -> int:
    return c.mux_157_ns + extra_mux_ns + c.flash_acc_ns + c.latch_setup_ns


def flash_execute_ns(c: TimingConstants, alu_ns: int) -> int:
    return c.latch_q_ns + alu_ns


def serial_total_ns(
    c: TimingConstants,
    alu_ns: int,
    *,
    phase_registered: bool = False,
    extra_mux_ns: int = 0,
) -> int:
    phase = c.phase_161_q_ns if phase_registered else 0
    return (
        phase
        + c.mux_157_ns
        + extra_mux_ns
        + c.flash_acc_ns
        + c.latch_setup_ns
        + c.latch_q_ns
        + alu_ns
    )


def budget_for_arch(arch: str, c: TimingConstants | None = None) -> ArchTimingBudget:
    c = c or load_constants("max")
    if arch == ARCH_BASELINE_FSM:
        alu = c.alu_sub_direct_ns
        execute = alu + DELAY_CPLD_REG_PENALTY
        return ArchTimingBudget(
            arch=arch,
            delay_alu_ns=alu,
            delay_fetch_ns=0,
            delay_execute_ns=execute,
            serial_total_ns=execute,
            pipelined_fetch_slack_ns=EXEC_HALF_NS,
            pipelined_execute_slack_ns=EXEC_HALF_NS - execute,
            pipelined_ok=execute <= EXEC_HALF_NS,
            serial_ok=execute <= EXEC_HALF_NS,
            schedule="CPLD registered @ phase edge",
            bottleneck="CPLD→ALU",
        )

    if arch == ARCH_COUNTER_TEMPLATE:
        alu = c.alu_sub_direct_ns
        execute = alu + DELAY_EXT_CTRL_PENALTY
        return ArchTimingBudget(
            arch=arch,
            delay_alu_ns=alu,
            delay_fetch_ns=0,
            delay_execute_ns=execute,
            serial_total_ns=execute,
            pipelined_fetch_slack_ns=EXEC_HALF_NS,
            pipelined_execute_slack_ns=EXEC_HALF_NS - execute,
            pipelined_ok=execute <= EXEC_HALF_NS,
            serial_ok=execute <= EXEC_HALF_NS,
            schedule="74HC glue comb (no Flash CW)",
            bottleneck="ext ctrl glue to ALU",
        )

    if arch == ARCH_FLASH_CW10:
        alu = c.alu_sub_decode_ns
        extra = 0
    elif arch == ARCH_FLASH_CW16:
        alu = c.alu_sub_direct_ns
        extra = 0
    else:
        alu = c.alu_sub_direct_ns
        extra = 0

    fetch = flash_fetch_ns(c, extra_mux_ns=extra)
    execute = flash_execute_ns(c, alu)
    serial = serial_total_ns(c, alu, extra_mux_ns=extra)
    serial_reg = serial_total_ns(c, alu, phase_registered=True, extra_mux_ns=extra)

    pipelined_ok = fetch <= EXEC_HALF_NS and execute <= EXEC_HALF_NS
    serial_ok = serial <= EXEC_HALF_NS

    if not pipelined_ok:
        if fetch > EXEC_HALF_NS:
            bottleneck = "CW fetch (mux+Flash+setup)"
        else:
            bottleneck = "Execute (574 Q→ALU)"
    elif not serial_ok:
        bottleneck = "serial same half-period"
    else:
        bottleneck = "none"

    schedule = (
        "pipelined: CW fetch prior half-cycle, 574 latch @ edge, ALU in execute half"
        if pipelined_ok
        else "pipelined FAIL"
    )

    return ArchTimingBudget(
        arch=arch,
        delay_alu_ns=alu,
        delay_fetch_ns=fetch,
        delay_execute_ns=execute,
        serial_total_ns=max(serial, serial_reg),
        pipelined_fetch_slack_ns=EXEC_HALF_NS - fetch,
        pipelined_execute_slack_ns=EXEC_HALF_NS - execute,
        pipelined_ok=pipelined_ok,
        serial_ok=serial_ok,
        schedule=schedule,
        bottleneck=bottleneck,
    )


def all_budgets(c: TimingConstants | None = None) -> list[ArchTimingBudget]:
    c = c or load_constants("max")
    return [
        budget_for_arch(ARCH_BASELINE_FSM, c),
        budget_for_arch(ARCH_FLASH_CW16, c),
        budget_for_arch(ARCH_FLASH_CW10, c),
        budget_for_arch(ARCH_COUNTER_TEMPLATE, c),
    ]


def print_report(budgets: list[ArchTimingBudget]) -> None:
    print(f"Execute half-period budget: {EXEC_HALF_NS} ns @ 2 MHz")
    print()
    hdr = (
        f"{'arch':<22} {'alu':>4} {'fetch':>5} {'exec':>5} "
        f"{'serial':>6} {'f_slk':>5} {'e_slk':>5} {'pipe':>4} {'ser':>4}"
    )
    print(hdr)
    print("-" * len(hdr))
    for b in budgets:
        print(
            f"{b.arch:<22} {b.delay_alu_ns:>4} {b.delay_fetch_ns:>5} {b.delay_execute_ns:>5} "
            f"{b.serial_total_ns:>6} {b.pipelined_fetch_slack_ns:>5} {b.pipelined_execute_slack_ns:>5} "
            f"{'OK' if b.pipelined_ok else 'FAIL':>4} {'OK' if b.serial_ok else 'FAIL':>4}"
        )
    print()
    for b in budgets:
        if b.arch.startswith("flash") or b.arch == ARCH_COUNTER_TEMPLATE:
            print(f"{b.arch}: {b.schedule}")
            if b.serial_total_ns > EXEC_HALF_NS:
                print(f"  serial same-half: {b.serial_total_ns} ns - not feasible")
            print(f"  bottleneck: {b.bottleneck}")


def write_json(path: Path, budgets: list[ArchTimingBudget], c: TimingConstants) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "exec_half_ns": EXEC_HALF_NS,
        "constants": asdict(c),
        "architectures": [asdict(b) for b in budgets],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Write build/research/.../flash_cw_timing.json")
    parser.add_argument("--timing", choices=("typ", "max"), default="max")
    args = parser.parse_args()

    c = load_constants(args.timing)
    budgets = all_budgets(c)
    print_report(budgets)

    if args.json:
        out = ROOT / "build" / "research" / "cpld-ctrl-extract" / "flash_cw_timing.json"
        write_json(out, budgets, c)
        print(f"\nWrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
