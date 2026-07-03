"""Generate alu8 functional-block YAML netlist (reference/alu8-phase-b.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

BLOCK_NAME = "alu8_func"
DESCRIPTION = "v1.0 ALU — functional blocks (MUX4 slice, ADD4, MUX2 Y, CMP glue)"


def _mux4_instance(bit: int) -> dict[str, Any]:
    i = bit
    return {
        "ref": f"U_MUX4_{i}",
        "part": "FB_MUX4_SLICE",
        "pins": {
            "A": f"net_a{i}",
            "B": f"net_b{i}",
            "C0": "net_lgc0",
            "C1": "net_lgc1",
            "C2": "net_lgc2",
            "C3": "net_lgc3",
            "D0": "net_bctrl0",
            "D1": "net_bctrl1",
            "D2": "net_bctrl2",
            "D3": "net_bctrl3",
            "Y_LOGIC": f"net_y_logic{i}",
            "Y_BADD": f"net_b_add{i}",
        },
    }


def _add4_instance(ref: str, a_lo: int, b_lo: int, s_lo: int, cin: str, cout: str) -> dict[str, Any]:
    pins: dict[str, str] = {
        "CIN": cin,
        "COUT": cout,
    }
    for n in range(4):
        pins[f"A{n}"] = f"net_a{a_lo + n}"
        pins[f"B{n}"] = f"net_b_add{b_lo + n}"
        pins[f"S{n}"] = f"net_sum{s_lo + n}"
    return {"ref": ref, "part": "FB_ADD4", "pins": pins}


def _mux2_instance(bit: int) -> dict[str, Any]:
    i = bit
    return {
        "ref": f"U_MUX2_Y_{i}",
        "part": "FB_MUX2_Y",
        "pins": {
            "A": f"net_sum{i}",
            "B": f"net_y_logic{i}",
            "S": "net_y_mux_sel",
            "Y": f"net_y{i}",
        },
    }


def build_alu8_func_netlist() -> dict[str, Any]:
    instances: list[dict[str, Any]] = []
    for i in range(8):
        instances.append(_mux4_instance(i))
    instances.append(_add4_instance("U_ADD_LO", 0, 0, 0, "net_cin", "net_c_lo"))
    instances.append(_add4_instance("U_ADD_HI", 4, 4, 4, "net_c_lo", "net_c_hi"))
    for i in range(8):
        instances.append(_mux2_instance(i))
    instances.append(
        {
            "ref": "U_Y_MUX_SEL",
            "part": "ALU_Y_MUX_SEL",
            "pins": {
                "S0": "net_153_s0",
                "S1": "net_153_s1",
                "SEL": "net_y_mux_sel",
            },
        }
    )
    instances.append(
        {
            "ref": "U_CMP_SUB",
            "part": "ALU_CMP_SUB",
            "pins": {
                **{f"Y{i}": f"net_y{i}" for i in range(8)},
                "C_HI": "net_c_hi",
                "CIN": "net_cin",
                "BCTRL0": "net_bctrl0",
                "BCTRL1": "net_bctrl1",
                "BCTRL2": "net_bctrl2",
                "BCTRL3": "net_bctrl3",
                "Z": "net_cmp_z",
                "C_GE": "net_cmp_c_ge",
            },
        }
    )

    nets: list[dict[str, Any]] = []
    for i in range(8):
        nets.append({"name": f"net_a{i}", "width": 1})
        nets.append({"name": f"net_b{i}", "width": 1})
    nets.append({"name": "net_cin", "width": 1})
    nets.append({"name": "net_153_s0", "width": 1})
    nets.append({"name": "net_153_s1", "width": 1})
    for i in range(4):
        nets.append({"name": f"net_bctrl{i}", "width": 1})
        nets.append({"name": f"net_lgc{i}", "width": 1})
    nets.append({"name": "net_y_mux_sel", "width": 1})
    nets.append({"name": "net_cmp_z", "width": 1, "probes": ["cmp_z"]})
    nets.append({"name": "net_cmp_c_ge", "width": 1, "probes": ["cmp_c_ge"]})
    for i in range(8):
        nets.append({"name": f"net_b_add{i}", "width": 1})
        nets.append({"name": f"net_sum{i}", "width": 1})
        nets.append({"name": f"net_y_logic{i}", "width": 1})
    for i in range(8):
        probes = ["y0"] if i == 0 else (["y7"] if i == 7 else None)
        entry: dict[str, Any] = {"name": f"net_y{i}", "width": 1}
        if probes:
            entry["probes"] = probes
        nets.append(entry)
    nets.append({"name": "net_c_lo", "width": 1})
    nets.append({"name": "net_c_hi", "width": 1, "probes": ["carry_hi"]})
    nets.append({"name": "pwr_vcc", "width": 1})
    nets.append({"name": "pwr_gnd", "width": 1})

    return {
        "version": 1,
        "block": BLOCK_NAME,
        "description": DESCRIPTION,
        "instances": instances,
        "nets": nets,
    }


def build_alu8_func_units() -> dict[str, Any]:
    units: list[dict[str, Any]] = []
    for i in range(8):
        units.append(
            {
                "id": f"mux4_bit_{i}",
                "kind": "mux4_bit",
                "label": f"FB_MUX4[{i}] logic+B",
                "stage": 2,
                "package_ref": f"U_MUX4_{i}",
            }
        )
    units.append(
        {
            "id": "add4_lo",
            "kind": "adder4",
            "label": "FB_ADD4 LO (a0-3)",
            "stage": 1,
            "package_ref": "U_ADD_LO",
        }
    )
    units.append(
        {
            "id": "add4_hi",
            "kind": "adder4",
            "label": "FB_ADD4 HI (a4-7)",
            "stage": 1,
            "package_ref": "U_ADD_HI",
        }
    )
    for i in range(8):
        units.append(
            {
                "id": f"mux2_y_{i}",
                "kind": "mux2_y",
                "label": f"FB_MUX2_Y y[{i}]",
                "stage": 4,
                "package_ref": f"U_MUX2_Y_{i}",
            }
        )
    units.append(
        {
            "id": "y_mux_sel",
            "kind": "y_mux_sel",
            "label": "ALU_Y_MUX_SEL",
            "stage": 0,
            "package_ref": "U_Y_MUX_SEL",
        }
    )
    units.append(
        {
            "id": "cmp_sub",
            "kind": "cmp_sub",
            "label": "ALU_CMP_SUB",
            "stage": 5,
            "package_ref": "U_CMP_SUB",
        }
    )
    return {"version": 1, "block": BLOCK_NAME, "units": units}


def _yaml_lines_mapping(mapping: dict[str, Any], indent: int) -> list[str]:
    sp = " " * indent
    lines: list[str] = []
    for key, val in mapping.items():
        if isinstance(val, dict):
            lines.append(f"{sp}{key}:")
            lines.extend(_yaml_lines_mapping(val, indent + 2))
        else:
            lines.append(f"{sp}{key}: {val}")
    return lines


def dump_yaml(data: dict[str, Any]) -> str:
    """Minimal YAML emitter for netlist/units dicts (no external deps)."""
    lines: list[str] = []

    for key, val in data.items():
        if isinstance(val, dict):
            lines.append(f"{key}:")
            lines.extend(_yaml_lines_mapping(val, 2))
        elif isinstance(val, list):
            lines.append(f"{key}:")
            for item in val:
                if not isinstance(item, dict):
                    lines.append(f"  - {item}")
                    continue
                lines.append("  -")
                for ik, iv in item.items():
                    if isinstance(iv, dict):
                        lines.append(f"    {ik}:")
                        lines.extend(_yaml_lines_mapping(iv, 6))
                    elif isinstance(iv, list):
                        lines.append(f"    {ik}:")
                        for sub in iv:
                            lines.append(f"      - {sub}")
                    else:
                        lines.append(f"    {ik}: {iv}")
        else:
            lines.append(f"{key}: {val}")

    return "\n".join(lines) + "\n"


def write_alu8_func_netlist(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(build_alu8_func_netlist()), encoding="utf-8")
    return path


def write_alu8_func_units(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(build_alu8_func_units()), encoding="utf-8")
    return path


def export_alu8_func(
    netlist_path: Path,
    units_path: Path | None = None,
) -> tuple[Path, Path | None]:
    write_alu8_func_netlist(netlist_path)
    units_out = None
    if units_path is not None:
        units_out = write_alu8_func_units(units_path)
    return netlist_path, units_out


def port_net_names() -> set[str]:
    """External port nets (matches archive alu8.yaml port set)."""
    names: set[str] = set()
    for i in range(8):
        names.add(f"net_a{i}")
        names.add(f"net_b{i}")
        names.add(f"net_y{i}")
    names.update(
        {
            "net_cin",
            "net_153_s0",
            "net_153_s1",
            "net_bctrl0",
            "net_bctrl1",
            "net_bctrl2",
            "net_bctrl3",
            "net_lgc0",
            "net_lgc1",
            "net_lgc2",
            "net_lgc3",
            "net_y_mux_sel",
            "net_cmp_z",
            "net_cmp_c_ge",
            "net_c_hi",
        }
    )
    return names
