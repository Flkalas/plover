"""Map view-units onto gate-level pins and nets in the full assembly schematic."""

from __future__ import annotations

from dataclasses import dataclass

from hwsim.export_schematic import (
    GATES_PER_CHIP,
    _instance_base,
    _instance_index,
    _logical_to_dip_pin,
    group_into_packages,
    load_pinout,
)
from hwsim.netlist import Netlist
from hwsim.units.catalog import ViewUnit
from hwsim.units.extract import UnitExtract, extract_unit


@dataclass(frozen=True)
class GatePin:
    pkg: str
    dip: int
    logical: str


@dataclass(frozen=True)
class UnitScope:
    unit_id: str
    nets: frozenset[str]
    gate_pins: frozenset[GatePin]
    instance_refs: frozenset[str]


def _assembly_package_for_ref(nl: Netlist, ref: str) -> str:
    inst = next(i for i in nl.instances if i.ref == ref)
    gpc = GATES_PER_CHIP.get(inst.part)
    if gpc:
        idx = _instance_index(ref)
        if idx is not None:
            base = _instance_base(ref, idx)
            pkg_idx = idx // gpc
            suffix = f"#{pkg_idx + 1}" if pkg_idx else ""
            return f"{base}{suffix}"
    if inst.part == "ALU_153_SLICE":
        bit = int(ref.rsplit("_", 1)[-1])
        chip = bit // 2
        return f"U_ALU_153_L_{chip}"
    return ref


def _153_mux_logical(mux: int, pin: str) -> str:
    if pin in ("A", "B", "VCC", "GND"):
        return pin
    if pin == "G":
        return f"{mux}G"
    if pin == "Y":
        return f"{mux}Y"
    if pin.startswith("C") and len(pin) == 2:
        return f"{mux}{pin}"
    return pin


def _157_bit_logical(bit_local: int, pin: str) -> str:
    if pin in ("A", "B", "Y"):
        return f"{bit_local}{pin}"
    return pin


def _add_gate_pin(
    out: list[GatePin],
    *,
    pkg: str,
    part: str,
    logical: str,
    gate: int | None = None,
) -> None:
    try:
        po = load_pinout(part)
    except FileNotFoundError:
        return
    dip = _logical_to_dip_pin(logical, gate, po)
    if dip is not None:
        out.append(GatePin(pkg=pkg, dip=dip, logical=logical))


def _gate_pins_from_extracted(
    nl: Netlist,
    unit: ViewUnit,
    extracted: UnitExtract,
) -> frozenset[GatePin]:
    pins: list[GatePin] = []
    pkg_part = extracted.package.part
    pin_map = {
        pin: net
        for pin, net in (
            (c[0], c[1])
            for c in extracted.package.connections
        )
    }

    if unit.kind == "not_gate":
        asm_pkg = _assembly_package_for_ref(nl, unit.package_ref)
        idx = _instance_index(unit.package_ref)
        gate = (idx % 6) + 1 if idx is not None else 1
        for logical in ("A", "Y"):
            if logical in pin_map:
                _add_gate_pin(pins, pkg=asm_pkg, part="74HC04", logical=logical, gate=gate)

    elif unit.kind == "mux4_b":
        mux = int(unit.slot.replace("mux", ""))
        asm_pkg = unit.package_ref
        for logical in pin_map:
            sym = _153_mux_logical(mux, logical)
            _add_gate_pin(pins, pkg=asm_pkg, part="74HC153", logical=sym)

    elif unit.kind == "mux4_l":
        bit = int(unit.package_ref.rsplit("_", 1)[-1])
        mux = (bit % 2) + 1
        asm_pkg = f"U_ALU_153_L_{bit // 2}"
        for logical in pin_map:
            sym = _153_mux_logical(mux, logical)
            _add_gate_pin(pins, pkg=asm_pkg, part="74HC153", logical=sym)

    elif unit.kind == "adder4":
        asm_pkg = unit.package_ref
        for pkg in group_into_packages(nl.instances, assembly=True):
            if pkg.id != asm_pkg:
                continue
            for logical, _net, gate in pkg.connections:
                _add_gate_pin(pins, pkg=asm_pkg, part="74HC283", logical=logical, gate=gate)
            break

    elif unit.kind == "mux2_y":
        bit_local = int(unit.slot.replace("bit", ""))
        asm_pkg = unit.package_ref
        for logical in pin_map:
            sym = _157_bit_logical(bit_local, logical)
            _add_gate_pin(pins, pkg=asm_pkg, part="74HC157", logical=sym, gate=bit_local)

    return frozenset(pins)


def unit_scope(nl: Netlist, unit: ViewUnit) -> UnitScope:
    extracted = extract_unit(nl, unit)
    nets = frozenset(p.net for p in extracted.boundary_ports)
    gate_pins = _gate_pins_from_extracted(nl, unit, extracted)

    refs: set[str] = {unit.package_ref}
    if unit.kind == "not_gate":
        refs.add(unit.package_ref)
    elif unit.kind == "mux4_l":
        refs.add(unit.package_ref)

    return UnitScope(
        unit_id=unit.id,
        nets=nets,
        gate_pins=gate_pins,
        instance_refs=frozenset(refs),
    )


def scope_to_manifest_entry(scope: UnitScope) -> dict:
    return {
        "nets": sorted(scope.nets),
        "gate_pins": [
            {"pkg": p.pkg, "dip": p.dip, "logical": p.logical}
            for p in sorted(scope.gate_pins, key=lambda x: (x.pkg, x.dip))
        ],
        "instance_refs": sorted(scope.instance_refs),
    }
