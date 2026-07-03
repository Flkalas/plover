"""Export alu8 12-DIP assembly netlist tests."""

from __future__ import annotations

import re
from pathlib import Path

from simulators.cyclesim.export.alu8_netlist import (
    build_alu8_func_netlist,
    build_alu8_func_units,
    export_alu8_func,
    port_net_names,
    write_alu8_func_netlist,
)


def _part_counts(netlist: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for inst in netlist["instances"]:
        part = inst["part"]
        counts[part] = counts.get(part, 0) + 1
    return counts


def test_instance_counts() -> None:
    counts = _part_counts(build_alu8_func_netlist())
    assert len(build_alu8_func_netlist()["instances"]) == 12
    assert counts["74HC153"] == 8
    assert counts["74HC283"] == 2
    assert counts["74HC157"] == 2


def test_port_nets_present() -> None:
    netlist = build_alu8_func_netlist()
    names = {n["name"] for n in netlist["nets"]}
    assert port_net_names() <= names


def test_topology_edges() -> None:
    nl = build_alu8_func_netlist()
    by_ref = {i["ref"]: i for i in nl["instances"]}
    assert by_ref["U_ALU_153_0"]["pins"]["2Y"] == "net_b_add0"
    assert by_ref["U_ALU_283_LO"]["pins"]["B0"] == "net_b_add0"
    assert by_ref["U_ALU_283_LO"]["pins"]["CIN"] == "net_cin"
    assert by_ref["U_ALU_283_LO"]["pins"]["COUT"] == "net_c_lo"
    assert by_ref["U_ALU_283_HI"]["pins"]["CIN"] == "net_c_lo"
    assert by_ref["U_ALU_157_YBP_0"]["pins"]["1A"] == "net_sum0"
    assert by_ref["U_ALU_157_YBP_0"]["pins"]["1B"] == "net_y_logic0"
    assert by_ref["U_ALU_157_YBP_0"]["pins"]["1Y"] == "net_y0"
    assert by_ref["U_ALU_157_YBP_0"]["pins"]["S"] == "net_y_mux_sel"
    assert "U_Y_MUX_SEL" not in by_ref
    assert "U_CMP_SUB" not in by_ref


def test_units_catalog() -> None:
    units = build_alu8_func_units()
    assert len(units["units"]) == 12
    kinds = {u["kind"] for u in units["units"]}
    assert kinds == {"hc153", "hc283", "hc157"}


def test_dump_and_export_files(tmp_path: Path) -> None:
    nl_path = tmp_path / "alu8_func.yaml"
    units_path = tmp_path / "alu8_func.units.yaml"
    export_alu8_func(nl_path, units_path)
    text = nl_path.read_text(encoding="utf-8")
    assert "74HC153" in text
    assert "1C0" in text
    assert "net_bctrl0" in text
    assert "block: alu8_func" in text
    assert units_path.read_text(encoding="utf-8").count("package_ref:") == 12


def test_write_roundtrip_keys(tmp_path: Path) -> None:
    path = tmp_path / "out.yaml"
    write_alu8_func_netlist(path)
    raw = path.read_text(encoding="utf-8")
    assert re.search(r"^version: 1$", raw, re.M)
    assert "instances:" in raw
    assert "nets:" in raw
