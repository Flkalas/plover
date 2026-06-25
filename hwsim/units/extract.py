"""Extract a single view-unit from a full netlist."""

from __future__ import annotations

from dataclasses import dataclass

from hwsim.export_schematic import (
    PWR_GND,
    PWR_VCC,
    POWER_PINS,
    PhysicalPackage,
    _normalize_net,
    _skip_connection,
)
from hwsim.netlist import Instance, Netlist
from hwsim.units.catalog import ViewUnit

OUTPUT_LOGICAL = frozenset({"Y", "C4", "S0", "S1", "S2", "S3"})
OUTPUT_PREFIXES = ("1Y", "2Y", "3Y", "4Y")


@dataclass(frozen=True)
class UnitBoundaryPort:
    net: str
    label: str
    direction: str  # "in" | "out"
    logical_pin: str


@dataclass(frozen=True)
class FixedPort:
    """Logic input tied to VCC/GND (not a routable net)."""

    logical_pin: str
    value: str  # "0" | "1"


@dataclass
class UnitExtract:
    unit: ViewUnit
    package: PhysicalPackage
    boundary_ports: list[UnitBoundaryPort]
    fixed_ports: list[FixedPort]


def _inst_by_ref(nl: Netlist) -> dict[str, Instance]:
    return {inst.ref: inst for inst in nl.instances}


def _port_direction(logical: str) -> str:
    if logical in OUTPUT_LOGICAL:
        return "out"
    if logical.endswith("Y") or logical in OUTPUT_PREFIXES:
        return "out"
    return "in"


def _label_for_net(net: str) -> str:
    return net.removeprefix("net_")


def _fixed_constant_ports(pins: dict[str, str]) -> list[FixedPort]:
    """Logic pins hard-wired to VCC/GND (chip power rails excluded)."""
    fixed: list[FixedPort] = []
    for pin, net in sorted(pins.items()):
        if pin in POWER_PINS:
            continue
        if net == PWR_VCC:
            fixed.append(FixedPort(logical_pin=pin, value="1"))
        elif net == PWR_GND:
            fixed.append(FixedPort(logical_pin=pin, value="0"))
    order = {"C0": 0, "C1": 1, "C2": 2, "C3": 3, "A": 4, "B": 5, "S": 6, "G": 7, "OE": 8}
    fixed.sort(key=lambda fp: order.get(fp.logical_pin, 99))
    return fixed


def _boundary_from_pins(pins: dict[str, str]) -> list[UnitBoundaryPort]:
    ports: list[UnitBoundaryPort] = []
    seen: set[str] = set()
    for pin, net in sorted(pins.items()):
        if pin in POWER_PINS:
            continue
        if _skip_connection(pin, net):
            continue
        n = _normalize_net(pin, net)
        if n in (PWR_VCC, PWR_GND) or n in seen:
            continue
        seen.add(n)
        ports.append(
            UnitBoundaryPort(
                net=n,
                label=_label_for_net(n),
                direction=_port_direction(pin),
                logical_pin=pin,
            )
        )
    ports.sort(key=lambda p: (0 if p.direction == "in" else 1, p.net))
    return ports


def _slice_153_b_mux(inst: Instance, mux: int) -> tuple[PhysicalPackage, dict[str, str]]:
    prefix = f"{mux}"
    pins: dict[str, str] = {}
    for pin, net in inst.pins.items():
        if pin in ("A", "B", "VCC", "GND"):
            pins[pin] = net
        elif pin.startswith(prefix):
            rest = pin[len(prefix) :]
            if rest in ("C0", "C1", "C2", "C3", "G", "Y"):
                mapped = "G" if rest == "G" else ("Y" if rest == "Y" else rest)
                pins[mapped] = net
    pkg = PhysicalPackage(
        id=f"{inst.ref}_mux{mux}",
        part="ALU_153_SLICE",
        instance_refs=[inst.ref],
    )
    for pin, net in pins.items():
        if not _skip_connection(pin, net):
            pkg.connections.append((pin, _normalize_net(pin, net), None))
    return pkg, pins


def _slice_157_bit(inst: Instance, bit_local: int) -> tuple[PhysicalPackage, dict[str, str]]:
    n = bit_local
    pins: dict[str, str] = {}
    for key in (f"{n}A", f"{n}B", f"{n}Y"):
        if key in inst.pins:
            logical = key[1:]
            pins[logical] = inst.pins[key]
    for key in ("S", "OE", "VCC", "GND"):
        if key in inst.pins:
            pins[key] = inst.pins[key]
    pkg = PhysicalPackage(
        id=f"{inst.ref}_y{n}",
        part="74HC157",
        instance_refs=[inst.ref],
    )
    for pin, net in pins.items():
        if not _skip_connection(pin, net):
            gate = n if pin in ("A", "B", "Y") else None
            pkg.connections.append((pin, _normalize_net(pin, net), gate))
    return pkg, pins


def _package_for_not(inst: Instance) -> tuple[PhysicalPackage, dict[str, str]]:
    pins = dict(inst.pins)
    pkg = PhysicalPackage(
        id=inst.ref,
        part=inst.part,
        instance_refs=[inst.ref],
    )
    for pin, net in pins.items():
        if not _skip_connection(pin, net):
            pkg.connections.append((pin, _normalize_net(pin, net), 1))
    return pkg, pins


def _package_whole(inst: Instance) -> tuple[PhysicalPackage, dict[str, str]]:
    pins = dict(inst.pins)
    pkg = PhysicalPackage(
        id=inst.ref,
        part=inst.part,
        instance_refs=[inst.ref],
    )
    for pin, net in pins.items():
        if not _skip_connection(pin, net):
            pkg.connections.append((pin, _normalize_net(pin, net), None))
    return pkg, pins


def extract_unit(nl: Netlist, unit: ViewUnit) -> UnitExtract:
    by_ref = _inst_by_ref(nl)
    inst = by_ref[unit.package_ref]

    if unit.kind == "not_gate":
        pkg, pins = _package_for_not(inst)
    elif unit.kind == "mux4_b":
        mux = int(unit.slot.replace("mux", ""))
        pkg, pins = _slice_153_b_mux(inst, mux)
    elif unit.kind == "mux4_l":
        pkg, pins = _package_whole(inst)
        pkg = PhysicalPackage(
            id=inst.ref,
            part="ALU_153_SLICE",
            instance_refs=[inst.ref],
        )
        for pin, net in inst.pins.items():
            if not _skip_connection(pin, net):
                pkg.connections.append((pin, _normalize_net(pin, net), None))
        pins = dict(inst.pins)
    elif unit.kind == "adder4":
        pkg, pins = _package_whole(inst)
    elif unit.kind == "mux2_y":
        bit_local = int(unit.slot.replace("bit", ""))
        pkg, pins = _slice_157_bit(inst, bit_local)
    elif unit.kind in (
        "and_gate",
        "or_gate",
        "not_gate",
        "counter4",
        "latch8",
        "decoder3x8",
        "rom16",
        "mux2_addr",
    ):
        pkg, pins = _package_whole(inst)
    else:
        raise ValueError(f"unsupported unit kind: {unit.kind}")

    return UnitExtract(
        unit=unit,
        package=pkg,
        boundary_ports=_boundary_from_pins(pins),
        fixed_ports=_fixed_constant_ports(pins),
    )
