"""Physical package pools and gate_assign application."""

from __future__ import annotations

import re

from hwsim.export_schematic import (
    GATES_PER_CHIP,
    PhysicalPackage,
    _alu153_slice_pin_to_153,
    _group_alu8_assembly,
    _instance_base,
    _instance_index,
    _normalize_net,
    _skip_connection,
    group_into_packages,
)
from hwsim.netlist import Instance, Netlist
from hwsim.placement.graph import GateUnit


class GateSlot:
    __slots__ = ("package_id", "part", "gate", "mux")

    def __init__(
        self,
        package_id: str,
        part: str,
        gate: int | None,
        mux: int | None = None,
    ) -> None:
        self.package_id = package_id
        self.part = part
        self.gate = gate
        self.mux = mux

    @property
    def key(self) -> str:
        if self.mux is not None:
            return f"mux{self.mux}"
        return str(self.gate or 0)


class PartFamily:
    __slots__ = ("part", "packages", "slots", "unit_refs")

    def __init__(
        self,
        part: str,
        packages: list[str],
        slots: list[GateSlot],
        unit_refs: list[str],
    ) -> None:
        self.part = part
        self.packages = packages
        self.slots = slots
        self.unit_refs = unit_refs


def default_packages(nl: Netlist, *, assembly: bool) -> list[PhysicalPackage]:
    return group_into_packages(nl.instances, assembly=assembly)


def _package_ids_for_part(packages: list[PhysicalPackage], part: str) -> list[str]:
    return sorted({p.id for p in packages if p.part == part})


def build_part_families(
    nl: Netlist,
    units: list[GateUnit],
    packages: list[PhysicalPackage],
    *,
    assembly: bool,
) -> dict[str, PartFamily]:
    by_part: dict[str, list[GateUnit]] = {}
    for u in units:
        by_part.setdefault(u.part, []).append(u)

    families: dict[str, PartFamily] = {}

    for part, part_units in by_part.items():
        if part == "ALU_153_SLICE" and assembly:
            pkg_ids = [p.id for p in packages if p.part == "74HC153" and "_L_" in p.id]
            pkg_ids = sorted(set(pkg_ids))
            slots = [
                GateSlot(package_id=pid, part="74HC153", gate=None, mux=m)
                for pid in pkg_ids
                for m in (1, 2)
            ]
            families["ALU_153_SLICE"] = PartFamily(
                part="ALU_153_SLICE",
                packages=pkg_ids,
                slots=slots,
                unit_refs=[u.ref for u in part_units],
            )
            continue

        gpc = GATES_PER_CHIP.get(part)
        if gpc:
            pkg_ids = _package_ids_for_part(packages, part)
            slots = [
                GateSlot(package_id=pid, part=part, gate=g)
                for pid in pkg_ids
                for g in range(1, gpc + 1)
            ]
            families[part] = PartFamily(
                part=part,
                packages=pkg_ids,
                slots=slots,
                unit_refs=[u.ref for u in part_units],
            )

    return families


def default_slot_for_ref(
    ref: str,
    part: str,
    packages: list[PhysicalPackage],
    *,
    assembly: bool,
) -> GateSlot | None:
    if part == "ALU_153_SLICE" and assembly:
        m = re.fullmatch(r"U_ALU_153_L_(\d+)", ref)
        if not m:
            return None
        bit = int(m.group(1))
        chip = bit // 2
        mux = (bit % 2) + 1
        return GateSlot(
            package_id=f"U_ALU_153_L_{chip}",
            part="74HC153",
            gate=None,
            mux=mux,
        )

    gpc = GATES_PER_CHIP.get(part)
    if not gpc:
        return None
    idx = _instance_index(ref)
    if idx is None:
        return None
    base = _instance_base(ref, idx)
    pkg_idx = idx // gpc
    gate = (idx % gpc) + 1
    suffix = f"#{pkg_idx + 1}" if pkg_idx else ""
    return GateSlot(package_id=f"{base}{suffix}", part=part, gate=gate)


def default_gate_assign(
    nl: Netlist,
    units: list[GateUnit],
    packages: list[PhysicalPackage],
    *,
    assembly: bool,
) -> dict[str, dict[str, dict[str, str]]]:
    out: dict[str, dict[str, dict[str, str]]] = {}
    for u in units:
        slot = default_slot_for_ref(u.ref, u.part, packages, assembly=assembly)
        if slot is None:
            continue
        out.setdefault(u.part, {}).setdefault(slot.package_id, {})[slot.key] = u.ref
    return out


def apply_gate_assign(
    nl: Netlist,
    gate_assign: dict[str, dict[str, dict[str, str]]],
    units: list[GateUnit],
    *,
    assembly: bool,
) -> list[PhysicalPackage]:
    inst_by_ref = {i.ref: i for i in nl.instances}
    result: list[PhysicalPackage] = []

    for part_key, by_pkg in gate_assign.items():
        if part_key == "ALU_153_SLICE":
            for pkg_id, slot_map in by_pkg.items():
                pkg = PhysicalPackage(id=pkg_id, part="74HC153")
                for slot_key, ref in slot_map.items():
                    mux = int(slot_key.replace("mux", ""))
                    inst = inst_by_ref[ref]
                    pkg.instance_refs.append(ref)
                    for pin, net in inst.pins.items():
                        if _skip_connection(pin, net):
                            continue
                        logical = _alu153_slice_pin_to_153(mux, pin)
                        pkg.connections.append((logical, _normalize_net(pin, net), None))
                result.append(pkg)
            continue

        for pkg_id, slot_map in by_pkg.items():
            pkg = PhysicalPackage(id=pkg_id, part=part_key)
            for slot_key, ref in slot_map.items():
                gate = int(slot_key)
                inst = inst_by_ref[ref]
                pkg.instance_refs.append(ref)
                for pin, net in inst.pins.items():
                    if _skip_connection(pin, net):
                        continue
                    pkg.connections.append((pin, _normalize_net(pin, net), gate))
            result.append(pkg)

    return result


def merge_packages_with_assign(
    nl: Netlist,
    gate_assign: dict[str, dict[str, dict[str, str]]],
    units: list[GateUnit],
    *,
    assembly: bool,
) -> list[PhysicalPackage]:
    """Default packages with gate_assign overrides for multi-gate / slice parts."""
    base = default_packages(nl, assembly=assembly)
    reassigned_ids: set[str] = set()
    reassigned_parts: set[str] = set(gate_assign.keys())

    for part_key, by_pkg in gate_assign.items():
        reassigned_ids.update(by_pkg.keys())

    kept: list[PhysicalPackage] = []
    for pkg in base:
        if pkg.id in reassigned_ids:
            continue
        if pkg.part in GATES_PER_CHIP and pkg.part in reassigned_parts:
            continue
        if "ALU_153_SLICE" in reassigned_parts and pkg.part == "74HC153" and "_L_" in pkg.id:
            continue
        kept.append(pkg)

    assigned = apply_gate_assign(nl, gate_assign, units, assembly=assembly)
    return kept + assigned
