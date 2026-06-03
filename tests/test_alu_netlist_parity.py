"""cyclesim alu8_decode netlist Y vs plover_vm alu8() for all alu8_cases vectors."""

from __future__ import annotations

from pathlib import Path

from cyclesim.engine import build_context
from plover_vm.alu import alu8
from tools.alu8_cases import CASES, bits, ctrl

ROOT = Path(__file__).resolve().parents[1]
NL = ROOT / "hw/netlist/blocks/alu8_decode.yaml"


def _read_y(ctx) -> int:
    return sum((ctx.get_net(f"net_y{i}") & 1) << i for i in range(8))


def _run_case(name: str, a: int, b: int, y_exp: int, control: dict[str, int], sel: int) -> None:
    ctx = build_context(NL, ROOT)
    ctx._stuck_nets.clear()
    ctx.reset_float_nets()
    mapping: dict[str, int] = {}
    mapping.update(bits("net_a", a))
    mapping.update(bits("net_b", b))
    mapping.update(control)
    for i in range(4):
        mapping[f"net_alu_op{i}"] = (sel >> i) & 1
    for net, val in mapping.items():
        ctx.set_net(net, val, stuck=True)
    ctx.comb_fixup()
    y_net = _read_y(ctx)
    assert y_net == y_exp, f"{name}: netlist Y={y_net:#x} expected={y_exp:#x}"
    y_alu = alu8(a, b, sel).y
    assert y_alu == y_exp, f"{name}: alu8()={y_alu:#x} expected={y_exp:#x}"
    assert y_net == y_alu, f"{name}: netlist vs alu8 {y_net:#x} != {y_alu:#x}"


def test_all_alu8_cases_match_netlist_and_alu8():
    for sel, (name, a, b, y_exp, c) in enumerate(CASES):
        _run_case(name, a, b, y_exp, c, sel)
