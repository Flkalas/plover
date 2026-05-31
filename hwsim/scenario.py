"""Programmatic hwsim scenarios (CW cycles → stimulus)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hwsim.netlist import load_netlist, load_timing
from hwsim.simulator import SimContext, VALUE_NAMES, _net_at_time, _run_check

CLOCK_PERIOD_NS = 500
MAX_INTERACTIVE_DURATION_NS = 5000

REG_NAMES = ("R0", "R1", "R2", "R3")


def _tools_root(repo_root: Path) -> Path:
    return repo_root / "tools"


def load_alu_opcodes(repo_root: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(_tools_root(repo_root)))
    try:
        from alu8_cases import CASES  # noqa: WPS433
    finally:
        sys.path.pop(0)
    return [{"id": i, "name": name, "hex": f"{i:X}"} for i, (name, *_rest) in enumerate(CASES)]


def cycle_to_set(
    alu_op: int,
    src_reg: int,
    dst_reg: int,
    bus_en: int = 0,
) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in range(4):
        out[f"net_alu_op{i}"] = (alu_op >> i) & 1
    for i in range(2):
        out[f"net_src_reg{i}"] = (src_reg >> i) & 1
        out[f"net_dst_reg{i}"] = (dst_reg >> i) & 1
        out[f"net_bus_en{i}"] = (bus_en >> i) & 1
    return out


def cycles_to_stimulus(
    cycles: list[dict[str, Any]],
    *,
    period_ns: int = CLOCK_PERIOD_NS,
    cmp_n_init: int = 1,
) -> tuple[list[dict[str, Any]], int]:
    stimulus: list[dict[str, Any]] = []
    if cmp_n_init:
        stimulus.append({"at_ns": 0, "set": {"net_cmp_n": int(cmp_n_init)}})
    for i, cyc in enumerate(cycles):
        at = i * period_ns
        s = cycle_to_set(
            int(cyc.get("alu_op", 0)),
            int(cyc.get("src_reg", 0)),
            int(cyc.get("dst_reg", 0)),
            int(cyc.get("bus_en", 0)),
        )
        stimulus.append({"at_ns": at, "set": s})
    duration = max(period_ns * len(cycles) + 400, period_ns)
    duration = min(duration, MAX_INTERACTIVE_DURATION_NS)
    return stimulus, duration


def preset_cycles(name: str) -> list[dict[str, Any]]:
    inc = 9
    add = 1
    if name == "clock_add_demo":
        return [
            {"alu_op": inc, "src_reg": 0, "dst_reg": 0},
            {"alu_op": inc, "src_reg": 2, "dst_reg": 2},
            {"alu_op": inc, "src_reg": 2, "dst_reg": 2},
            {"alu_op": add, "src_reg": 0, "dst_reg": 2},
        ]
    raise KeyError(name)


def byte_from_final(final: dict[str, str], prefix: str) -> int:
    val = 0
    for i in range(8):
        bit = final.get(f"{prefix}{i}", "0")
        if bit == "1":
            val |= 1 << i
    return val


def enrich_result(result: dict[str, Any]) -> dict[str, Any]:
    final = result.get("final_nets", {})
    registers = {REG_NAMES[r]: byte_from_final(final, f"net_r{r}_q") for r in range(4)}
    alu_y = byte_from_final(final, "net_y")
    cmp_n = final.get("net_cmp_n", "1")
    result = dict(result)
    result["registers"] = registers
    result["alu_y"] = alu_y
    result["cw_decode"] = {
        "net_cmp_n": cmp_n,
        "net_sub_en": final.get("net_sub_en", "?"),
    }
    return result


def run_scenario(
    netlist_path: Path,
    repo_root: Path,
    *,
    stimulus: list[dict[str, Any]],
    duration_ns: int,
    timing: str = "max",
    expect: list[dict[str, Any]] | None = None,
    checks: list[dict[str, Any]] | None = None,
    test_name: str = "scenario",
) -> dict[str, Any]:
    nl = load_netlist(netlist_path)
    mode = timing
    tdata = load_timing(repo_root, mode)
    ctx = SimContext(nl, tdata)

    probe_nets = nl.probe_nets() or {n.name for n in nl.nets if not n.name.startswith("pwr_")}

    for stim in stimulus:
        at = int(stim.get("at_ns", 0))
        payload: dict[str, Any] = {}
        if "set" in stim:
            payload["set"] = {k: int(v) for k, v in stim["set"].items()}
        if "toggle" in stim:
            payload["toggle"] = [stim["toggle"]] if isinstance(stim["toggle"], str) else list(stim["toggle"])
        ctx.scheduler.schedule(at, "stimulus", **payload)

    ctx.run(duration_ns)

    errors: list[str] = []
    for exp in expect or []:
        at = int(exp.get("at_ns", 0))
        for net, want in exp.items():
            if net == "at_ns":
                continue
            got = _net_at_time(ctx, net, at)
            if got != int(want):
                errors.append(f"at {at}ns {net}: expected {want} got {VALUE_NAMES.get(got, got)}")

    check_results: list[dict[str, Any]] = []
    for chk in checks or []:
        cr = _run_check(chk, ctx, duration_ns, errors)
        check_results.append(cr)

    waves = {n: ctx.wave.samples.get(n, []) for n in sorted(probe_nets) if n in ctx.wave.samples}

    return {
        "test": test_name,
        "block": nl.block,
        "timing_mode": mode,
        "duration_ns": duration_ns,
        "passed": len(errors) == 0,
        "errors": errors,
        "violations": ctx.violations,
        "checks": check_results,
        "waves": waves,
        "final_nets": {k: VALUE_NAMES.get(v, "?") for k, v in ctx.nets.items()},
    }


def simulate_request(body: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    preset = body.get("preset")
    if preset and preset != "custom":
        cycles = preset_cycles(str(preset))
    else:
        cycles = list(body.get("cycles") or [])
    if not cycles:
        raise ValueError("cycles required (or use preset)")

    period = int(body.get("period_ns", CLOCK_PERIOD_NS))
    stimulus, duration = cycles_to_stimulus(cycles, period_ns=period)
    timing = str(body.get("timing", "max"))

    view_nl = repo_root / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_view.yaml"
    clock_nl = repo_root / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_clock.yaml"
    netlist_path = view_nl if view_nl.is_file() else clock_nl

    result = run_scenario(
        netlist_path,
        repo_root,
        stimulus=stimulus,
        duration_ns=duration,
        timing=timing,
        checks=body.get("checks"),
        test_name=str(preset or "custom"),
    )
    return enrich_result(result)
