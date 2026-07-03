"""View-unit catalog for ALU8 gate-combination schematics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hwsim import yaml_util
from hwsim.netlist import Netlist

UNIT_KINDS = frozenset(
    {
        "not_gate",
        "mux4_b",
        "mux4_l",
        "mux4_bit",
        "adder4",
        "mux2_y",
        "and_gate",
        "or_gate",
        "counter4",
        "latch8",
        "decoder3x8",
        "mux2_addr",
        "rom16",
    }
)

CATEGORY_LABELS = {
    "not_gate": "NOT (~B)",
    "mux4_b": "MUX B-path",
    "mux4_l": "MUX Logic",
    "mux4_bit": "MUX bit-slice",
    "adder4": "4-bit Adder",
    "mux2_y": "Y bypass",
    "and_gate": "AND",
    "or_gate": "OR",
    "counter4": "Counter",
    "latch8": "Latch 8",
    "decoder3x8": "Decoder 3:8",
    "mux2_addr": "Addr MUX",
    "rom16": "Flash CW",
}


@dataclass(frozen=True)
class ViewUnit:
    id: str
    kind: str
    label: str
    stage: int
    package_ref: str
    slot: str = ""

    def category(self) -> str:
        return CATEGORY_LABELS.get(self.kind, self.kind)


def _build_alu8_units() -> list[ViewUnit]:
    units: list[ViewUnit] = []

    for i in range(8):
        units.append(
            ViewUnit(
                id=f"mux4_bit_{i}",
                kind="mux4_bit",
                label=f"153[{i}] logic+B",
                stage=2,
                package_ref=f"U_ALU_153_{i}",
            )
        )

    for ref, label in (("U_ALU_283_LO", "283 LO (a0-3)"), ("U_ALU_283_HI", "283 HI (a4-7)")):
        units.append(
            ViewUnit(
                id=ref.removeprefix("U_ALU_").lower(),
                kind="adder4",
                label=label,
                stage=1,
                package_ref=ref,
            )
        )

    for bit in range(8):
        chip = bit // 4
        local = (bit % 4) + 1
        units.append(
            ViewUnit(
                id=f"mux2_y_{bit}",
                kind="mux2_y",
                label=f"157_YBP y[{bit}]",
                stage=4,
                package_ref=f"U_ALU_157_YBP_{chip}",
                slot=f"bit{local}",
            )
        )

    return units


def _unit_from_dict(raw: dict) -> ViewUnit:
    return ViewUnit(
        id=str(raw["id"]),
        kind=str(raw["kind"]),
        label=str(raw["label"]),
        stage=int(raw["stage"]),
        package_ref=str(raw["package_ref"]),
        slot=str(raw.get("slot", "")),
    )


def catalog_to_yaml(units: list[ViewUnit]) -> str:
    lines = ["version: 1", "block: alu8", "units:"]
    for u in units:
        lines.append(f"  - id: {u.id}")
        lines.append(f"    kind: {u.kind}")
        lines.append(f"    label: {u.label}")
        lines.append(f"    stage: {u.stage}")
        lines.append(f"    package_ref: {u.package_ref}")
        if u.slot:
            lines.append(f"    slot: {u.slot}")
    return "\n".join(lines) + "\n"


def load_catalog(path: Path) -> list[ViewUnit]:
    data = yaml_util.load_file(str(path))
    raw_units = data.get("units", [])
    return [_unit_from_dict(u) for u in raw_units]


def load_alu8_catalog(path: Path | None = None) -> list[ViewUnit]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "hw" / "units" / "alu8.yaml"
    if path.is_file():
        return load_catalog(path)
    return _build_alu8_units()


def validate_catalog(nl: Netlist, units: list[ViewUnit]) -> list[str]:
    errors: list[str] = []
    refs = {inst.ref for inst in nl.instances}
    ids: set[str] = set()
    for unit in units:
        if unit.id in ids:
            errors.append(f"duplicate unit id: {unit.id}")
        ids.add(unit.id)
        if unit.kind not in UNIT_KINDS:
            errors.append(f"{unit.id}: unknown kind {unit.kind}")
        if unit.package_ref not in refs:
            errors.append(f"{unit.id}: missing package_ref {unit.package_ref}")
        if unit.kind in ("mux4_b", "mux2_y", "mux2_addr") and not unit.slot:
            errors.append(f"{unit.id}: slot required for {unit.kind}")
    return errors
