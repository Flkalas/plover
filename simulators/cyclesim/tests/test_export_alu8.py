"""Export alu8 functional-block netlist tests."""

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
    assert counts["FB_MUX4_SLICE"] == 8
    assert counts["FB_ADD4"] == 2
    assert counts["FB_MUX2_Y"] == 8
    assert counts["ALU_Y_MUX_SEL"] == 1
    assert counts["ALU_CMP_SUB"] == 1


def test_port_nets_present() -> None:
    netlist = build_alu8_func_netlist()
    names = {n["name"] for n in netlist["nets"]}
    assert port_net_names() <= names


def test_topology_edges() -> None:
    nl = build_alu8_func_netlist()
    by_ref = {i["ref"]: i for i in nl["instances"]}
    assert by_ref["U_MUX4_0"]["pins"]["Y_BADD"] == "net_b_add0"
    assert by_ref["U_ADD_LO"]["pins"]["B0"] == "net_b_add0"
    assert by_ref["U_ADD_LO"]["pins"]["CIN"] == "net_cin"
    assert by_ref["U_ADD_LO"]["pins"]["COUT"] == "net_c_lo"
    assert by_ref["U_ADD_HI"]["pins"]["CIN"] == "net_c_lo"
    assert by_ref["U_MUX2_Y_0"]["pins"]["A"] == "net_sum0"
    assert by_ref["U_MUX2_Y_0"]["pins"]["B"] == "net_y_logic0"
    assert by_ref["U_MUX2_Y_0"]["pins"]["Y"] == "net_y0"
    assert by_ref["U_Y_MUX_SEL"]["pins"]["SEL"] == "net_y_mux_sel"


def test_units_catalog() -> None:
    units = build_alu8_func_units()
    assert len(units["units"]) == 20
    kinds = {u["kind"] for u in units["units"]}
    assert kinds == {"mux4_bit", "adder4", "mux2_y", "y_mux_sel", "cmp_sub"}


def test_dump_and_export_files(tmp_path: Path) -> None:
    nl_path = tmp_path / "alu8_func.yaml"
    units_path = tmp_path / "alu8_func.units.yaml"
    export_alu8_func(nl_path, units_path)
    text = nl_path.read_text(encoding="utf-8")
    assert "FB_MUX4_SLICE" in text
    assert "net_bctrl0" in text
    assert "block: alu8_func" in text
    assert units_path.read_text(encoding="utf-8").count("package_ref:") == 20


def test_write_roundtrip_keys(tmp_path: Path) -> None:
    path = tmp_path / "out.yaml"
    write_alu8_func_netlist(path)
    raw = path.read_text(encoding="utf-8")
    assert re.search(r"^version: 1$", raw, re.M)
    assert "instances:" in raw
    assert "nets:" in raw
