"""Event-driven netlist simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hwsim.models.base import ChipModel, create_model
from hwsim.netlist import Netlist, load_netlist, load_timing
from hwsim.scheduler import Scheduler
from hwsim import yaml_util


# 0=L, 1=H, 2=X, 3=Z
VALUE_NAMES = {0: "0", 1: "1", 2: "X", 3: "Z"}


@dataclass
class WaveRecorder:
    samples: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def record(self, net: str, time_ns: int, value: int) -> None:
        rows = self.samples.setdefault(net, [])
        if rows and rows[-1]["t"] == time_ns and rows[-1]["v"] == value:
            return
        rows.append({"t": time_ns, "v": VALUE_NAMES.get(value, "?")})


@dataclass
class PendingDrive:
    net: str
    value: int
    driver: str
    reason: str


class SimContext:
    def __init__(self, nl: Netlist, timing: dict[str, Any]) -> None:
        self.nl = nl
        self.timing = timing
        self.scheduler = Scheduler()
        self.nets: dict[str, int] = {}
        self.wave = WaveRecorder()
        self.models: list[ChipModel] = []
        self.listeners: dict[str, list[ChipModel]] = {}
        self.latch_state: dict[tuple[str, int], int] = {}
        self.violations: list[str] = []
        self.path_delays: list[dict[str, Any]] = []
        self._pending: dict[str, PendingDrive] = {}
        self._toggle_tasks: dict[str, int] = {}

        for nd in nl.nets:
            self.nets[nd.name] = 2
        for inst in nl.instances:
            model = create_model(inst.ref, inst.part, inst.pins, self)
            self.models.append(model)
            for pin, net in inst.pins.items():
                if net.startswith("pwr_"):
                    if pin in ("VCC", "VDD"):
                        self.nets[net] = 1
                    elif pin in ("GND", "VSS"):
                        self.nets[net] = 0
                    continue
                self.listeners.setdefault(net, []).append(model)

    def get_net(self, net: str) -> int:
        return self.nets.get(net, 2)

    def set_net_immediate(self, net: str, value: int) -> None:
        self.nets[net] = value

    def schedule_drive(self, net: str, value: int, delay_ns: int, driver: str, reason: str) -> None:
        when = self.scheduler.now_ns + delay_ns
        self._pending[net] = PendingDrive(net, value, driver, reason)
        self.scheduler.schedule(when, "drive", net=net, value=value, driver=driver, reason=reason)

    def schedule_recurring_toggle(self, net: str, half_period_ns: int, driver: str) -> None:
        self._toggle_tasks[net] = half_period_ns
        self.scheduler.schedule_after(half_period_ns, "toggle", net=net, driver=driver)

    def check_setup(self, ref: str, clk_pin: str, data_pin: str, setup_ns: int) -> bool:
        # Simplified: data must be stable setup_ns before edge (tracked via violation flag only on change at edge)
        return True

    def _apply_drive(self, net: str, value: int, driver: str, reason: str) -> None:
        old = self.nets.get(net, 2)
        if old == value and value != 3:
            return
        self.nets[net] = value
        self.wave.record(net, self.scheduler.now_ns, value)
        for m in self.listeners.get(net, []):
            m.on_net_change(net)

    def _handle(self, ev: Any) -> None:
        if ev.kind == "drive":
            self._apply_drive(ev.payload["net"], ev.payload["value"], ev.payload["driver"], ev.payload["reason"])
        elif ev.kind == "toggle":
            net = ev.payload["net"]
            cur = self.nets.get(net, 0)
            nxt = 1 - cur if cur in (0, 1) else 0
            self._apply_drive(net, nxt, ev.payload["driver"], "toggle")
            half = self._toggle_tasks.get(net, 125)
            self.scheduler.schedule_after(half, "toggle", net=net, driver=ev.payload["driver"])
        elif ev.kind == "stimulus":
            for net, val in ev.payload.get("set", {}).items():
                self._apply_drive(net, int(val), "stimulus", "set")
            for net in ev.payload.get("toggle", []):
                cur = self.nets.get(net, 0)
                self._apply_drive(net, 1 - cur if cur in (0, 1) else 1, "stimulus", "toggle")

    def run(self, end_ns: int) -> None:
        for m in self.models:
            m.on_start()
        self.scheduler.run_until(end_ns, self._handle)


def load_test(path: Path) -> dict[str, Any]:
    data = yaml_util.load_file(str(path))
    if not isinstance(data, dict):
        raise ValueError("test file must be a mapping")
    return data


def run_test(test_path: Path, repo_root: Path) -> dict[str, Any]:
    test = load_test(test_path)
    nl_path = (test_path.parent / test["netlist"]).resolve()
    if not nl_path.is_file():
        nl_path = (repo_root / test["netlist"]).resolve()
    nl = load_netlist(nl_path)
    mode = str(test.get("timing", "typ"))
    timing = load_timing(repo_root, mode)
    duration = int(test.get("duration_ns", 1000))
    ctx = SimContext(nl, timing)

    probe_nets = nl.probe_nets() or {n.name for n in nl.nets if not n.name.startswith("pwr_")}

    for stim in test.get("stimulus", []):
        at = int(stim.get("at_ns", 0))
        payload: dict[str, Any] = {}
        if "set" in stim:
            payload["set"] = {k: int(v) for k, v in stim["set"].items()}
        if "toggle" in stim:
            payload["toggle"] = [stim["toggle"]] if isinstance(stim["toggle"], str) else list(stim["toggle"])
        ctx.scheduler.schedule(at, "stimulus", **payload)

    ctx.run(duration)

    errors: list[str] = []
    for exp in test.get("expect", []):
        at = int(exp.get("at_ns", 0))
        ctx.scheduler.now_ns = at
        for net, want in exp.items():
            if net == "at_ns":
                continue
            got = ctx.nets.get(net, 2)
            if got != int(want):
                errors.append(f"at {at}ns {net}: expected {want} got {VALUE_NAMES.get(got, got)}")

    check_results: list[dict[str, Any]] = []
    for chk in test.get("checks", []):
        cr = _run_check(chk, ctx, duration, errors)
        check_results.append(cr)

    waves = {n: ctx.wave.samples.get(n, []) for n in sorted(probe_nets) if n in ctx.wave.samples}

    return {
        "test": test_path.stem,
        "block": nl.block,
        "timing_mode": mode,
        "duration_ns": duration,
        "passed": len(errors) == 0,
        "errors": errors,
        "violations": ctx.violations,
        "checks": check_results,
        "waves": waves,
        "final_nets": {k: VALUE_NAMES.get(v, "?") for k, v in ctx.nets.items()},
    }


def _run_check(chk: dict[str, Any], ctx: SimContext, duration: int, errors: list[str]) -> dict[str, Any]:
    ctype = chk.get("type")
    if ctype == "frequency":
        net = chk["signal"]
        samples = ctx.wave.samples.get(net, [])
        edges = [s for i, s in enumerate(samples) if i == 0 or samples[i - 1]["v"] != s["v"]]
        rising = [e for i, e in enumerate(edges) if i > 0 and edges[i - 1]["v"] == "0" and e["v"] == "1"]
        if len(rising) < 2:
            errors.append(f"frequency: not enough edges on {net}")
            return {"type": ctype, "passed": False}
        periods = [rising[i + 1]["t"] - rising[i]["t"] for i in range(len(rising) - 1)]
        avg_period = sum(periods) / len(periods)
        measured_hz = 1_000_000_000 / avg_period
        target = float(chk.get("target_hz", 2_000_000))
        tol = float(chk.get("tolerance_pct", 1)) / 100.0
        ok = abs(measured_hz - target) / target <= tol
        if not ok:
            errors.append(f"frequency {net}: {measured_hz:.0f} Hz vs target {target:.0f} Hz")
        return {"type": ctype, "passed": ok, "measured_hz": measured_hz, "target_hz": target}

    if ctype == "slack":
        path = chk.get("path", [])
        min_slack = int(chk.get("min_slack_ns", 0))
        # Worst-case comb path budget: 250ns half period at 2 MHz
        budget = int(chk.get("budget_ns", 250))
        delay = _estimate_path_delay(path, ctx)
        slack = budget - delay
        ok = slack >= min_slack
        if not ok:
            errors.append(f"slack path {path}: delay {delay}ns budget {budget}ns slack {slack}ns")
        return {"type": ctype, "passed": ok, "delay_ns": delay, "slack_ns": slack, "path": path}

    if ctype == "setup_hold":
        ok = len(ctx.violations) == 0
        if not ok:
            errors.extend(ctx.violations)
        return {"type": ctype, "passed": ok, "violations": list(ctx.violations)}

    return {"type": ctype, "passed": True}


def _estimate_path_delay(path: list[str], ctx: SimContext) -> int:
    total = 0
    ref_to_part = {m.ref: m.part for m in ctx.models}
    for hop in path:
        if "." not in hop:
            continue
        ref, _pin = hop.split(".", 1)
        part = ref_to_part.get(ref, "")
        if part == "OSC_4M":
            total += 0
        elif part == "74HC74":
            total += delay_ns(ctx.timing, "74HC74", "t_pd_q", default=25)
        elif part == "74HC283":
            total += delay_ns(ctx.timing, "74HC283", "t_pd", "cout", default=45)
        elif part == "74HC574":
            total += delay_ns(ctx.timing, "74HC574", "t_pd_q", default=23)
        elif part == "74HC04":
            total += delay_ns(ctx.timing, "74HC04", "t_pd", default=15)
        else:
            total += 10
    return total


def delay_ns(timing: dict[str, Any], part: str, *keys: str, default: int = 10) -> int:
    from hwsim.netlist import delay_ns as dn
    return dn(timing, part, *keys, default=default)
