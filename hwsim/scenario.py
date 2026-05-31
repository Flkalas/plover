"""Programmatic hwsim scenarios (stimulus → simulation)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hwsim.netlist import load_netlist, load_timing
from hwsim.simulator import SimContext, VALUE_NAMES, _net_at_time, _run_check


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
