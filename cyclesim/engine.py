"""Micro-phase cycle engine — zero-delay comb fixpoint + clock edges."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cyclesim.models.base import L, X, Z
from cyclesim.models.registry import create_model, is_sequential_part
from cyclesim.trace import WaveTrace
from hwsim.netlist import Netlist, load_netlist, validate_netlist

FIXPOINT_LIMIT = 64


@dataclass
class CycleContext:
    nl: Netlist
    nets: dict[str, int] = field(default_factory=dict)
    models: list[Any] = field(default_factory=list)
    comb_models: list[Any] = field(default_factory=list)
    seq_models: list[Any] = field(default_factory=list)
    regfile: Any | None = None
    trace: WaveTrace = field(default_factory=WaveTrace)
    violations: list[str] = field(default_factory=list)
    _pin_map: dict[tuple[str, str], str] = field(default_factory=dict)
    _stuck_nets: set[str] = field(default_factory=set)

    @classmethod
    def from_netlist(cls, nl: Netlist) -> CycleContext:
        ctx = cls(nl=nl)
        for nd in nl.nets:
            ctx.nets[nd.name] = X
        for inst in nl.instances:
            if inst.part.startswith("pwr") or inst.part in ("OSC_4M",):
                continue
            model = create_model(inst.ref, inst.part, inst.pins, ctx)
            ctx.models.append(model)
            if is_sequential_part(inst.part):
                ctx.seq_models.append(model)
                if inst.part in ("REGFILE_574_GPR", "CPLD_REGFILE"):
                    ctx.regfile = model
            else:
                ctx.comb_models.append(model)
            for pin, net in inst.pins.items():
                if net.startswith("pwr_"):
                    if pin in ("VCC", "VDD"):
                        ctx.nets[net] = 1
                    elif pin in ("GND", "VSS"):
                        ctx.nets[net] = 0
                    continue
                ctx._pin_map[(inst.ref, pin)] = net
        return ctx

    def get_net(self, net: str) -> int:
        return self.nets.get(net, X)

    def set_net(self, net: str, value: int, stuck: bool = False) -> None:
        self.nets[net] = value
        if stuck:
            self._stuck_nets.add(net)

    _pending: dict[str, tuple[int, str]] = field(default_factory=dict, repr=False)

    def drive_net(self, net: str, value: int, driver: str) -> bool:
        if net in self._stuck_nets:
            return False
        prev = self._pending.get(net)
        if prev is not None and prev[0] != value and value != Z and prev[0] != Z:
            self._pending[net] = (X, driver)
            return True
        self._pending[net] = (value, driver)
        return True

    def _flush_pending(self) -> bool:
        changed = False
        for net, (val, _drv) in self._pending.items():
            if net in self._stuck_nets:
                continue
            old = self.nets.get(net, X)
            if old != val:
                changed = True
            self.nets[net] = val
        self._pending.clear()
        return changed

    def reset_float_nets(self) -> None:
        for name in self.nets:
            if name.startswith("pwr_"):
                continue
            if name not in self._stuck_nets:
                self.nets[name] = X
        self._pending.clear()

    def comb_fixup(self) -> None:
        for _ in range(FIXPOINT_LIMIT):
            self._pending.clear()
            for m in self.comb_models:
                m.eval_comb()
            for m in self.seq_models:
                m.eval_comb()
            if not self._flush_pending():
                return
        self.violations.append("comb fixpoint did not converge")

    def pulse_clock(self) -> None:
        clk_net = self._find_clk_net()
        if not clk_net:
            return
        self.set_net(clk_net, L)
        self.comb_fixup()
        self.set_net(clk_net, 1)
        for m in self.seq_models:
            m.eval_clock("posedge")
        self.comb_fixup()
        self.set_net(clk_net, L)
        self.comb_fixup()
        for m in self.seq_models:
            if hasattr(m, "_prev_clk"):
                m._prev_clk = L

    def _find_clk_net(self) -> str | None:
        for nd in self.nl.nets:
            if nd.name == "net_clk" or "clk" in (nd.probes or []):
                return nd.name
        return "net_clk" if "net_clk" in self.nets else None

    def bus_byte(self, prefix: str) -> int | None:
        val = 0
        for i in range(8):
            v = self.get_net(f"{prefix}{i}")
            if v > 1:
                return None
            val |= (v & 1) << i
        return val

    def apply_set(self, mapping: dict[str, int]) -> None:
        for net, val in mapping.items():
            self.set_net(net, val & 1 if val <= 1 else val, stuck=True)


def build_context(netlist_path: Path, repo_root: Path) -> CycleContext:
    nl = load_netlist(netlist_path)
    errors = validate_netlist(nl, repo_root)
    if errors:
        raise ValueError("; ".join(errors[:5]))
    return CycleContext.from_netlist(nl)
