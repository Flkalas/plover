"""153 bit-slice assembly packages (one DIP per bit)."""

from pathlib import Path

from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS, group_into_packages
from hwsim.netlist import load_netlist


def test_153_bit_slice_eight_packages():
    root = Path(__file__).resolve().parents[1]
    nl = load_netlist(root / "hw/netlist/blocks/alu8.yaml")
    pkgs = group_into_packages(nl.instances, assembly=True)
    bit_pkgs = [p for p in pkgs if p.part == "74HC153" and p.id.startswith("U_ALU_153_")]
    assert len(bit_pkgs) == 8
    ids = sorted(p.id for p in bit_pkgs)
    assert ids == [f"U_ALU_153_{i}" for i in range(8)]
    for p in bit_pkgs:
        assert len(p.instance_refs) == 1
        assert "1Y" in {c[0] for c in p.connections}
        assert "2Y" in {c[0] for c in p.connections}
