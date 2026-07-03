"""Tests for placement graph."""

from pathlib import Path

from hwsim.netlist import load_netlist
from hwsim.placement.graph import build_gate_units, net_hypergraph
from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS, group_into_packages


def test_alu8_gate_units():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    reassignable = [u for u in units if u.part in ("74HC04",)]
    assert len(reassignable) == 8  # 8x 04 inverters (153 are native 74HC153)
    refs = {u.ref for u in units if u.part == "74HC04"}
    assert len(refs) == 8


def test_net_hypergraph_fanout():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    hg = net_hypergraph(units)
    assert "net_b0" in hg
    assert len(hg["net_lgc0"]) >= 8
