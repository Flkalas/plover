"""Netlist loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hwsim import yaml_util

POWER_PINS = frozenset({"VCC", "VDD", "GND", "VSS", "PWR", "PWR_VCC", "PWR_GND"})

KNOWN_PARTS = frozenset(
    {
        "OSC_4M",
        "74HC04",
        "74HC08",
        "74HC32",
        "74HC86",
        "74HC151",
        "74HC153",
        "74HC157",
        "74HC161",
        "74HC245",
        "74HC283",
        "74HC574",
        "74HC74",
        "74HC138",
        "SST39SF010A",
        "IS62C256",
        "ROM16",
        "ROM_CTRL",
        "PC8_AUTO",
        "FLG_LATCH",
        "CYCLE_FSM",
        "CPLD_REGFILE",
        "ATF1504AS",
        "CPLD_SYSTEM_CTRL",
        "REGFILE_574_GPR",
        "MAILBOX_MMIO",
    }
)


@dataclass
class Instance:
    ref: str
    part: str
    pins: dict[str, str]


@dataclass
class NetDef:
    name: str
    width: int = 1
    probes: list[str] = field(default_factory=list)


@dataclass
class Netlist:
    version: int
    block: str
    instances: list[Instance]
    nets: list[NetDef]
    path: Path | None = None

    def net_map(self) -> dict[str, NetDef]:
        return {n.name: n for n in self.nets}

    def probe_nets(self) -> set[str]:
        out: set[str] = set()
        for n in self.nets:
            if n.probes:
                out.add(n.name)
        return out


def load_netlist(path: Path) -> Netlist:
    raw = yaml_util.load_file(str(path))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected mapping at top level")
    instances = []
    for item in raw.get("instances", []):
        if not isinstance(item, dict):
            continue
        instances.append(
            Instance(
                ref=str(item["ref"]),
                part=str(item["part"]),
                pins={str(k): str(v) for k, v in dict(item.get("pins", {})).items()},
            )
        )
    nets = []
    for item in raw.get("nets", []):
        if isinstance(item, dict):
            nets.append(
                NetDef(
                    name=str(item["name"]),
                    width=int(item.get("width", 1)),
                    probes=[str(p) for p in item.get("probes", []) or []],
                )
            )
        elif isinstance(item, str):
            nets.append(NetDef(name=item, width=1))
    return Netlist(
        version=int(raw.get("version", 1)),
        block=str(raw.get("block", path.stem)),
        instances=instances,
        nets=nets,
        path=path,
    )


def validate_netlist(nl: Netlist, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if nl.version != 1:
        errors.append(f"unsupported netlist version {nl.version}")
    net_names = {n.name for n in nl.nets}
    connected: set[str] = set()
    refs: set[str] = set()
    for inst in nl.instances:
        if inst.ref in refs:
            errors.append(f"duplicate ref {inst.ref}")
        refs.add(inst.ref)
        if inst.part not in KNOWN_PARTS:
            errors.append(f"{inst.ref}: unknown part {inst.part}")
        for pin, net in inst.pins.items():
            if pin in POWER_PINS or net.startswith("pwr_"):
                continue
            if net not in net_names:
                errors.append(f"{inst.ref}.{pin} -> unknown net {net}")
            connected.add(net)
    for n in nl.nets:
        if n.name.startswith("pwr_"):
            continue
        if n.name not in connected:
            errors.append(f"unconnected net {n.name}")
    return errors


def load_timing(repo_root: Path, mode: str = "typ") -> dict[str, Any]:
    timing: dict[str, Any] = {}
    for name in ("74hc.yaml", "memory.yaml", "cpld.yaml"):
        path = repo_root / "hw" / "timing" / name
        if path.is_file():
            data = yaml_util.load_file(str(path))
            if isinstance(data, dict):
                timing.update(data)
    return _resolve_timing_mode(timing, mode)


def _resolve_timing_mode(timing: dict[str, Any], mode: str) -> dict[str, Any]:
    key = "max_ns" if mode == "max" else "typ_ns"
    resolved: dict[str, Any] = {}
    for part, spec in timing.items():
        if not isinstance(spec, dict):
            resolved[part] = spec
            continue
        flat: dict[str, Any] = {}
        for k, v in spec.items():
            if k == "source":
                flat[k] = v
                continue
            if isinstance(v, dict) and key in v:
                flat[k] = v[key]
            elif isinstance(v, dict) and "typ_ns" in v:
                flat[k] = v.get(key, v["typ_ns"])
            else:
                flat[k] = v
        resolved[part] = flat
    return resolved


def delay_ns(timing: dict[str, Any], part: str, *keys: str, default: int = 10) -> int:
    spec = timing.get(part, {})
    if not isinstance(spec, dict):
        return default
    node: Any = spec
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return default
    if isinstance(node, int):
        return node
    return default
