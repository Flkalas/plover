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
        self._pin_map: dict[tuple[str, str], str] = {}
        self.rom_image: list[int] = []

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
                self._pin_map[(inst.ref, pin)] = net
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
        edge_ns = self.scheduler.now_ns
        data_net = self._pin_map.get((ref, data_pin))
        if not data_net:
            return True
        last_chg = _last_transition_before(self.wave.samples.get(data_net, []), edge_ns)
        if last_chg is not None and last_chg > edge_ns - setup_ns:
            msg = (
                f"setup violation {ref}.{data_pin} ({data_net}) at {edge_ns}ns: "
                f"last change {last_chg}ns, need {setup_ns}ns stable"
            )
            self.violations.append(msg)
            return False
        return True

    def _apply_drive(self, net: str, value: int, driver: str, reason: str) -> None:
        old = self.nets.get(net, 2)
        if old == value and value != 3 and reason != "stimulus":
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


def load_rom_image(test: dict[str, Any], test_path: Path, repo_root: Path) -> list[int]:
    if "rom_image" in test:
        out: list[int] = []
        for w in test["rom_image"]:
            out.append(int(w, 16) if isinstance(w, str) else int(w))
        return out
    if "rom_image_file" not in test:
        return []
    rel = test["rom_image_file"]
    path = (test_path.parent / rel).resolve()
    if not path.is_file():
        path = (repo_root / rel).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"rom_image_file not found: {rel}")
    words: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        words.append(int(line, 16))
    return words


def run_test(test_path: Path, repo_root: Path) -> dict[str, Any]:
    from hwsim.scenario import run_scenario

    test = load_test(test_path)
    nl_path = (test_path.parent / test["netlist"]).resolve()
    if not nl_path.is_file():
        nl_path = (repo_root / test["netlist"]).resolve()
    mode = str(test.get("timing", "typ"))
    duration = int(test.get("duration_ns", 1000))
    stimulus = test.get("stimulus", [])
    for stim in stimulus:
        if "set" in stim:
            stim["set"] = {k: int(v) for k, v in stim["set"].items()}
    return run_scenario(
        nl_path,
        repo_root,
        stimulus=stimulus,
        duration_ns=duration,
        timing=mode,
        expect=test.get("expect"),
        checks=test.get("checks"),
        test_name=test_path.stem,
        rom_image=load_rom_image(test, test_path, repo_root),
    )


def _last_transition_before(rows: list[dict[str, Any]], before_ns: int) -> int | None:
    last: int | None = None
    for i in range(1, len(rows)):
        if rows[i]["t"] > before_ns:
            break
        if rows[i]["v"] != rows[i - 1]["v"]:
            last = rows[i]["t"]
    return last


def _first_transition_after(rows: list[dict[str, Any]], after_ns: int) -> int | None:
    for i in range(1, len(rows)):
        if rows[i]["t"] < after_ns:
            continue
        if rows[i]["v"] != rows[i - 1]["v"]:
            return rows[i]["t"]
    return None


def _stable_time(rows: list[dict[str, Any]], after_ns: int, want: str | None = None) -> int | None:
    """First time at or after after_ns when net holds stable value (optional want)."""
    val: str | None = None
    stable_from: int | None = None
    for i, row in enumerate(rows):
        if row["t"] < after_ns:
            val = row["v"]
            continue
        if i > 0 and rows[i - 1]["v"] != row["v"]:
            stable_from = None
        if want is not None and row["v"] != want:
            stable_from = None
            val = row["v"]
            continue
        if stable_from is None:
            stable_from = row["t"]
        if row["t"] >= after_ns and stable_from is not None:
            return stable_from
    return stable_from


def _measure_path_delay(ctx: SimContext, from_net: str, to_net: str, after_ns: int) -> int | None:
    from_rows = ctx.wave.samples.get(from_net, [])
    to_rows = ctx.wave.samples.get(to_net, [])
    t0 = _first_transition_after(from_rows, after_ns)
    if t0 is None:
        t0 = after_ns

    t1 = _first_transition_after(to_rows, t0)
    if t1 is not None:
        return t1 - t0

    final_v = ctx.nets.get(to_net)
    if final_v not in (0, 1):
        return None
    want = VALUE_NAMES[final_v]
    stable = _stable_time(to_rows, t0, want)
    if stable is not None and stable >= t0:
        return stable - t0
    return None


def _net_at_time(ctx: SimContext, net: str, at_ns: int) -> int:
    rows = ctx.wave.samples.get(net, [])
    if not rows:
        return ctx.nets.get(net, 2)
    rev = {"0": 0, "1": 1, "X": 2, "Z": 3}
    result = 2
    for row in rows:
        if row["t"] > at_ns:
            break
        result = rev.get(row["v"], 2)
    return result


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

    if ctype == "path_delay":
        from_net = str(chk["from_net"])
        to_net = str(chk["to_net"])
        after_ns = int(chk.get("after_ns", 0))
        max_delay = int(chk.get("max_delay_ns", 250))
        measured = _measure_path_delay(ctx, from_net, to_net, after_ns)
        if measured is None:
            errors.append(f"path_delay {from_net}->{to_net}: could not measure")
            return {"type": ctype, "passed": False}
        ok = measured <= max_delay
        if not ok:
            errors.append(f"path_delay {from_net}->{to_net}: {measured}ns > {max_delay}ns")
        return {
            "type": ctype,
            "passed": ok,
            "measured_ns": measured,
            "max_delay_ns": max_delay,
            "from_net": from_net,
            "to_net": to_net,
        }

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
        ref, pin = hop.split(".", 1)
        part = ref_to_part.get(ref, "")
        if _is_path_output(part, pin):
            total += _hop_delay(ctx, part, pin)
    return total


def _is_path_output(part: str, pin: str) -> bool:
    if pin in ("Y", "Q"):
        return True
    if len(pin) == 2 and pin[0] in "1234" and pin[1] == "Y":
        return True
    if part == "74HC283" and pin.startswith("C") and pin not in ("Cin",):
        return True
    if part == "74HC574" and pin.startswith("Q"):
        return True
    if part == "ROM16" and pin.startswith("D"):
        return True
    return False


def _hop_delay(ctx: SimContext, part: str, pin: str) -> int:
    if part == "OSC_4M":
        return 0
    if part == "74HC74":
        return delay_ns(ctx.timing, "74HC74", "t_pd_q", default=25)
    if part == "74HC283":
        if pin in ("C4", "C0") or pin.startswith("C"):
            return delay_ns(ctx.timing, "74HC283", "t_pd", "cout", default=45)
        return delay_ns(ctx.timing, "74HC283", "t_pd", "sum", default=45)
    if part == "74HC574":
        if pin == "CP":
            return delay_ns(ctx.timing, "74HC574", "t_setup", default=8)
        return delay_ns(ctx.timing, "74HC574", "t_pd_q", default=23)
    if part == "74HC04":
        return delay_ns(ctx.timing, "74HC04", "t_pd", default=15)
    if part == "74HC08":
        return delay_ns(ctx.timing, "74HC08", "t_pd", default=15)
    if part == "74HC32":
        return delay_ns(ctx.timing, "74HC32", "t_pd", default=15)
    if part == "74HC86":
        return delay_ns(ctx.timing, "74HC86", "t_pd", default=15)
    if part == "74HC151":
        return delay_ns(ctx.timing, "74HC151", "t_pd", default=28)
    if part == "74HC153":
        return delay_ns(ctx.timing, "74HC153", "t_pd", default=28)
    if part == "74HC157":
        return delay_ns(ctx.timing, "74HC157", "t_pd", default=18)
    if part == "ROM16":
        return delay_ns(ctx.timing, "ROM16", "t_pd", default=40)
    if part == "PC8_AUTO":
        return delay_ns(ctx.timing, "PC8_AUTO", "t_clk_to_q", default=15)
    return 10


def delay_ns(timing: dict[str, Any], part: str, *keys: str, default: int = 10) -> int:
    from hwsim.netlist import delay_ns as dn
    return dn(timing, part, *keys, default=default)
