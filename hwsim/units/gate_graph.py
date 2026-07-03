"""Gate-level connectivity graph for ALU8 view-units."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hwsim.export_schematic import PWR_GND, PWR_VCC, _is_control_net
from hwsim.netlist import Netlist
from hwsim.units.catalog import ViewUnit
from hwsim.units.extract import extract_unit

B_OPERAND_BITS = tuple(f"net_b{i}" for i in range(8))
A_OPERAND_BITS = tuple(f"net_a{i}" for i in range(8))

IO_CONTROL = frozenset(
    {
        "net_cin",
        "net_bctrl0",
        "net_bctrl1",
        "net_bctrl2",
        "net_bctrl3",
        "net_lgc0",
        "net_lgc1",
        "net_lgc2",
        "net_lgc3",
        "net_153_s0",
        "net_153_s1",
        "net_y_mux_sel",
        "net_cmp_z",
        "net_cmp_c_ge",
    }
)

# Nets that exist in netlist but stay inside the ALU block (no IO stub).
INTERNAL_NET_PREFIXES = (
    "net_b_add",
    "net_sum",
    "net_y_logic",
)
INTERNAL_NETS = frozenset({"net_c_lo", "net_c_hi"})

_B_BIT_RE = re.compile(r"^net_b(\d+)$")


def is_b_operand_bit_net(net: str) -> bool:
    """Physical per-bit B operand nets (net_b0..net_b7), not sel/add/inv."""
    m = _B_BIT_RE.match(net)
    return m is not None


def is_a_operand_bit_net(net: str) -> bool:
    return net.startswith("net_a") and net[5:].isdigit()


@dataclass
class GatePort:
    unit_id: str
    net: str
    direction: str  # in | out
    logical: str


@dataclass
class GateGraph:
    units: dict[str, ViewUnit]
    ports: list[GatePort]
    net_to_ports: dict[str, list[GatePort]] = field(default_factory=dict)

    def external_nets(self) -> frozenset[str]:
        ext: set[str] = set()
        for net, plist in self.net_to_ports.items():
            if net in (PWR_VCC, PWR_GND) or not is_external_net(net):
                continue
            ext.add(net)
        return frozenset(ext)


def build_gate_graph(nl: Netlist, units: list[ViewUnit]) -> GateGraph:
    ports: list[GatePort] = []
    unit_map = {u.id: u for u in units}
    net_to_ports: dict[str, list[GatePort]] = {}

    for unit in units:
        extracted = extract_unit(nl, unit)
        for bp in extracted.boundary_ports:
            gp = GatePort(
                unit_id=unit.id,
                net=bp.net,
                direction=bp.direction,
                logical=bp.logical_pin,
            )
            ports.append(gp)
            net_to_ports.setdefault(bp.net, []).append(gp)

    return GateGraph(units=unit_map, ports=ports, net_to_ports=net_to_ports)


def is_external_net(net: str) -> bool:
    if net in IO_CONTROL:
        return True
    if net in INTERNAL_NETS:
        return False
    if any(net.startswith(p) for p in INTERNAL_NET_PREFIXES):
        return False
    if is_b_operand_bit_net(net):
        return True
    if is_a_operand_bit_net(net):
        return True
    if net.startswith("net_y") and not net.startswith("net_y_logic"):
        return True
    if net in ("net_cin",):
        return True
    return False
