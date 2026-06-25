"""Tests for ALU decode search and gate-cost scoring."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu_decode_arch import (
    ARCH_CW_DIRECT,
    ARCH_HC154,
    ARCH_SOP,
    dominates,
    pack_dips,
    pareto_front,
    score_all_architectures,
    score_architecture,
    score_hc154,
    score_sop,
)
from alu_decode_cost import score_truth_table
from alu_decode_model import (
    PROFILE_LEGACY,
    PROFILE_LGC_DIRECT,
    PROFILE_MINIMAL,
    PROFILE_Y_MUX,
    build_table,
    current_assignment,
    default_lgc_direct_arith,
    merge_lgc_direct,
    profile_options,
    profile_outputs,
    verify_signatures_match_cases,
)
from alu_decode_search import candidate_dict, score_assignment, search, search_lgc_direct
from alu_decode_model import lgc_direct_logic_assignment
from alu_opcode_decode import truth_table as legacy_truth_table
from alu8_cases import CASES
from gen_alu_decode_netlist import NetlistGen, legacy_gate_count
from plover_vm.alu import alu8


def test_signatures_match_alu8_cases():
    verify_signatures_match_cases()


def test_legacy_score_matches_netlist_gen():
    rows = legacy_truth_table()
    gen = NetlistGen()
    gen_cost = gen.gate_count(rows, cmp_op=11)
    scored = legacy_gate_count(rows, cmp_op=11)
    assert gen_cost == scored
    assert gen_cost.total == 166


def test_y_mux_profile_not_worse_than_legacy():
    cur = current_assignment()
    legacy = score_assignment(cur, PROFILE_LEGACY)
    y_mux = score_assignment(cur, PROFILE_Y_MUX)
    assert legacy is not None and y_mux is not None
    assert y_mux.total <= legacy.total
    assert y_mux.total == 154


def test_minimal_profile_cheaper_than_y_mux():
    cur = current_assignment()
    y_mux = score_assignment(cur, PROFILE_Y_MUX)
    minimal = score_assignment(cur, PROFILE_MINIMAL)
    assert y_mux is not None and minimal is not None
    assert minimal.total < y_mux.total
    assert minimal.total == 104


def test_build_table_sub_cmp_distinct_codes():
    assign = dict(current_assignment())
    rows, cmp_op = build_table(assign, PROFILE_Y_MUX)
    assert cmp_op == 11
    assert rows[2]["net_cin"] == rows[11]["net_cin"] == 1
    assert rows[2]["net_b_sel"] == rows[11]["net_b_sel"] == 1


def test_alu8_y_unchanged_under_assignment_permutation():
    """Y only depends on alu_sel index, not control-net names ??sanity for search."""
    name, a, b, y_exp, _c = CASES[2]
    assert alu8(a, b, 2).y == y_exp
    name, a, b, y_exp, _c = CASES[11]
    assert alu8(a, b, 11).y == y_exp


def test_search_finds_leq_cost_candidate():
    cur = current_assignment()
    baseline = score_assignment(cur, PROFILE_Y_MUX)
    assert baseline is not None
    found = search(PROFILE_Y_MUX, iterations=5_000, seed=42, top=5)
    assert found
    best = found[0]["cost"]["total"]
    assert best <= baseline.total


def test_lgc_direct_logic_opcodes_match_wire():
    fixed = lgc_direct_logic_assignment()
    assert fixed["AND"] == 0x1
    assert fixed["XOR"] == 0x6
    assert fixed["OR"] == 0x7
    assert fixed["NOT"] == 0x8
    assert fixed["PASS_A"] == fixed["AND"]


def test_lgc_direct_exhaustive_finds_optimal():
    found = search_lgc_direct(top=1)
    assert found
    assert found[0]["cost"]["total"] == 37


def test_lgc_direct_better_than_minimal_sop():
    cur = current_assignment()
    minimal = score_assignment(cur, PROFILE_MINIMAL)
    best = search_lgc_direct(top=1)[0]
    assert best["cost"]["total"] < minimal.total


def test_sop_dip_packing():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    sop = score_sop(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    assert sop.gates == 37
    assert sop.dips == 9


def test_hc154_lgc_direct_default():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    hc = score_hc154(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    assert hc.parts["74HC154"] == 1
    assert hc.parts.get("74HC00", 0) == 4  # 4 NAND gates
    decode_dips = pack_dips({"74HC154": 1, "74HC00": hc.parts.get("74HC00", 0)})
    assert decode_dips <= 2
    assert hc.advanced_blocks == 1


def test_hc154_glue_semantics():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    by_op = {r["op"]: r for r in rows}
    assert by_op[0x0B]["net_cin"] == 1
    assert by_op[0x0F]["net_cin"] == 1
    assert by_op[0x0B]["net_b_sel"] == by_op[0x0E]["net_b_sel"] == by_op[0x0F]["net_b_sel"] == 1
    assert by_op[0x0D]["net_b_const_sel"] == by_op[0x0E]["net_b_const_sel"] == 1
    hc = score_hc154(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    assert hc.parts.get("74HC00", 0) == 4


def test_cw_direct_zero_cost():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    cw = score_architecture(ARCH_CW_DIRECT, rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    assert cw.dips == 0
    assert cw.gates == 0
    assert cw.advanced_blocks == 0


def test_pareto_cw_dominates_sop():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    costs = score_all_architectures(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    assert dominates(costs[ARCH_CW_DIRECT], costs[ARCH_SOP])


def test_pareto_exhaustive_regression():
    found = search_lgc_direct(top=1)
    assert found
    assert found[0]["cost"]["total"] == 37


def test_candidate_dict_has_arch_costs():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    cand = candidate_dict(assign, PROFILE_LGC_DIRECT)
    assert "costs" in cand
    assert ARCH_HC154 in cand["costs"]
    assert "recommended_arch" in cand


def test_pareto_front_nonempty():
    assign = merge_lgc_direct(default_lgc_direct_arith())
    rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
    costs = score_all_architectures(rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op)
    entries = [("a", arch, costs[arch]) for arch in costs]
    front = pareto_front(entries)
    assert front
    archs_on_front = {a for _k, a, _c in front}
    assert ARCH_CW_DIRECT in archs_on_front


def test_lgc_direct_parallel_matches_serial():
  serial = search_lgc_direct(top=3, workers=1)
  parallel = search_lgc_direct(top=3, workers=2)
  assert serial[0]["cost"]["total"] == parallel[0]["cost"]["total"] == 37
  assert serial[0]["assignment"] == parallel[0]["assignment"]
