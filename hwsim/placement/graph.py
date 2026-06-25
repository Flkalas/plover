"""Netlist ??gate-level connectivity graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from hwsim.export_schematic import POWER_PINS, _normalize_net, _skip_connection
from hwsim.netlist import Instance, Netlist

PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"


@dataclass(frozen=True)
class GateUnit:
    ref: str
    part: str
    pins: dict[str, str]
    signal_nets: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_instance(cls, inst: Instance) -> GateUnit:
        nets: set[str] = set()
        for pin, net in inst.pins.items():
            if pin in POWER_PINS:
                continue
            if _skip_connection(pin, net):
                continue
            n = _normalize_net(pin, net)
            if n not in (PWR_VCC, PWR_GND):
                nets.add(n)
        return cls(ref=inst.ref, part=inst.part, pins=dict(inst.pins), signal_nets=frozenset(nets))


def build_gate_units(nl: Netlist, *, skip_refs: frozenset[str] | None = None) -> list[GateUnit]:
    skip = skip_refs or frozenset()
    out: list[GateUnit] = []
    for inst in nl.instances:
        if inst.ref in skip:
            continue
        if inst.part in ("ALU_CMP_SUB",) or inst.ref.endswith("Y_MUX_SEL"):
            continue
        out.append(GateUnit.from_instance(inst))
    return out


def net_hypergraph(units: list[GateUnit]) -> dict[str, list[str]]:
    """net ??list of gate refs connected."""
    hg: dict[str, list[str]] = {}
    for u in units:
        for net in u.signal_nets:
            hg.setdefault(net, []).append(u.ref)
    return hg


def external_io_nets(nl: Netlist) -> frozenset[str]:
    """Nets that connect to breadboard I/O panel."""
    from hwsim.export_schematic import _IO_SECTIONS

    defined = {n.name for n in nl.nets}
    nets: set[str] = set()
    for _title, section in _IO_SECTIONS:
        for net in section:
            if net in defined:
                nets.add(net)
    return frozenset(nets)
