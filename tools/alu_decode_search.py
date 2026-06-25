#!/usr/bin/env python3
"""Search alu_op assignments and decode output profiles to minimize decode cost.

Supports SOP gate count and multi-architecture Pareto ranking (DIP, advanced blocks, gates).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu_decode_arch import (
    ARCHITECTURES,
    ARCH_SOP,
    ArchCost,
    assignment_key,
    pareto_front,
    recommend_arch,
    score_all_architectures,
    score_architecture,
)
from alu_decode_cost import DecodeCost, score_truth_table
from alu_decode_model import (
    PROFILE_LEGACY,
    PROFILE_LGC_DIRECT,
    PROFILE_MINIMAL,
    PROFILE_Y_MUX,
    PROFILES,
    ARITH_GROUPS,
    OP_NAMES,
    assignment_notes,
    breaking_changes,
    build_table,
    current_assignment,
    default_lgc_direct_arith,
    lgc_direct_logic_assignment,
    lgc_from_opcode_direct,
    logic_reserved_codes,
    merge_lgc_direct,
    profile_options,
    profile_outputs,
    verify_signatures_match_cases,
)
from alu_opcode_decode import truth_table as legacy_truth_table
from gen_alu_decode_netlist import NetlistGen, legacy_gate_count

# Per-architecture pool size when building Pareto front from exhaustive search.
PARETO_POOL_PER_ARCH = 200


def default_workers() -> int:
    raw = os.environ.get("ALU_DECODE_JOBS")
    if raw is not None:
        return max(1, int(raw))
    return max(1, os.cpu_count() or 1)


def _lgc_direct_perm_codes() -> tuple[list[int], list[str]]:
    reserved = logic_reserved_codes()
    available = [c for c in range(16) if c not in reserved]
    group_names = list(ARITH_GROUPS.keys())
    return available, group_names


def _eval_lgc_direct_perm(payload: tuple[tuple[int, ...], list[str], tuple[str, ...], bool]) -> (
    tuple[int, DecodeCost, dict[str, int], dict[str, ArchCost] | None] | None
):
    """Worker: score one arithmetic opcode permutation (picklable for ProcessPoolExecutor)."""
    codes, group_names, arches, use_pareto = payload
    arith = dict(zip(group_names, codes))
    if arith["sub"] == arith["cmp"]:
        return None
    assign = merge_lgc_direct(arith)
    cost = score_assignment(assign, PROFILE_LGC_DIRECT)
    if cost is None:
        return None
    arch_costs: dict[str, ArchCost] | None = None
    if use_pareto:
        rows, cmp_op = build_table(assign, PROFILE_LGC_DIRECT)
        arch_costs = score_all_architectures(
            rows, PROFILE_LGC_DIRECT, cmp_op=cmp_op, arches=arches
        )
    return (cost.total, cost, assign, arch_costs)


def _run_lgc_direct_perms(
    *,
    arches: tuple[str, ...],
    use_pareto: bool,
    workers: int,
) -> list[tuple[int, DecodeCost, dict[str, int], dict[str, ArchCost] | None]]:
    available, group_names = _lgc_direct_perm_codes()
    payloads = [
        (codes, group_names, arches, use_pareto)
        for codes in permutations(available, len(group_names))
    ]
    if workers <= 1:
        out: list[Any] = []
        for payload in payloads:
            row = _eval_lgc_direct_perm(payload)
            if row is not None:
                out.append(row)
        return out

    chunksize = max(1, len(payloads) // (workers * 8))
    results: list[tuple[int, DecodeCost, dict[str, int], dict[str, ArchCost] | None]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for row in pool.map(_eval_lgc_direct_perm, payloads, chunksize=chunksize):
            if row is not None:
                results.append(row)
    return results


def _pareto_pool_from_evaluated(
    evaluated: list[tuple[int, DecodeCost, dict[str, int], dict[str, ArchCost] | None]],
    arches: tuple[str, ...],
    *,
    pool_per_arch: int = PARETO_POOL_PER_ARCH,
) -> list[dict[str, int]]:
    """Keep top layouts per architecture metric ??avoids O(n^2) on full exhaustive set."""
    by_arch: dict[str, list[tuple[tuple[int, int, int], dict[str, int]]]] = {a: [] for a in arches}
    for _total, _cost, assign, arch_costs in evaluated:
        if not arch_costs:
            continue
        for arch in arches:
            c = arch_costs[arch]
            if c.feasible:
                by_arch[arch].append((c.lex_key(), assign))
    seen: set[str] = set()
    pool: list[dict[str, int]] = []
    for arch in arches:
        ranked = sorted(by_arch[arch], key=lambda x: x[0])
        for _key, assign in ranked[:pool_per_arch]:
            akey = assignment_key(assign)
            if akey in seen:
                continue
            seen.add(akey)
            pool.append(assign)
    return pool


def score_assignment(assignment: dict[str, int], profile: str) -> DecodeCost | None:
    try:
        rows, cmp_op = build_table(assignment, profile)
    except ValueError:
        return None
    opts = profile_options(profile)
    return score_truth_table(
        rows,
        profile_outputs(profile),
        cmp_op=cmp_op,
        **opts,
    )


def _row_hex(row: dict, outputs: list[str]) -> str:
    bits = 0
    for i, sig in enumerate(outputs):
        bits |= int(row.get(sig, 0)) << i
    return f"op={row['op']:02x} ctrl={bits:03x}"


def candidate_dict(
    assignment: dict[str, int],
    profile: str,
    *,
    arches: tuple[str, ...] = ARCHITECTURES,
    pareto_rank: int | None = None,
    recommended: str | None = None,
) -> dict:
    rows, cmp_op = build_table(assignment, profile)
    outputs = profile_outputs(profile)
    cost = score_truth_table(rows, outputs, cmp_op=cmp_op, **profile_options(profile))
    arch_costs = score_all_architectures(rows, profile, cmp_op=cmp_op, arches=arches)
    rec = recommended or recommend_arch(arch_costs)
    out: dict = {
        "profile": profile,
        "cost": {"n04": cost.n04, "n08": cost.n08, "n32": cost.n32, "total": cost.total},
        "costs": {k: v.as_dict() for k, v in arch_costs.items()},
        "recommended_arch": rec,
        "assignment": dict(sorted(assignment.items())),
        "cmp_op": cmp_op,
        "breaking": breaking_changes(assignment),
        "notes": assignment_notes(assignment),
        "truth_table": [_row_hex(r, outputs) for r in rows],
    }
    if pareto_rank is not None:
        out["pareto_rank"] = pareto_rank
    if profile == PROFILE_LGC_DIRECT:
        out["logic_fixed"] = {k: f"0x{v:01x}" for k, v in sorted(lgc_direct_logic_assignment().items())}
        out["lgc_wire"] = "alu_op[0]->lgc3, [1]->lgc2, [2]->lgc1, [3]->lgc0"
        out["local_gates"] = "y_mux=OR(lgc*); b_const_hi hardwired in 153_B"
    return out


def random_assignment(rng: random.Random) -> dict[str, int]:
    codes = list(range(16))
    rng.shuffle(codes)
    assignment = {name: codes[i] for i, name in enumerate(OP_NAMES)}
    if assignment["SUB"] == assignment["CMP"]:
        assignment["CMP"] = next(c for c in range(16) if c != assignment["SUB"])
    return assignment


def neighbor(assignment: dict[str, int], rng: random.Random) -> dict[str, int]:
    out = dict(assignment)
    if rng.random() < 0.5:
        a, b = rng.sample(OP_NAMES, 2)
        out[a], out[b] = out[b], out[a]
    else:
        name = rng.choice(OP_NAMES)
        used = set(out.values())
        free = [c for c in range(16) if c not in used or c == out[name]]
        if not free:
            free = list(range(16))
        out[name] = rng.choice(free)
    if out["SUB"] == out["CMP"]:
        pool = [c for c in range(16) if c != out["SUB"]]
        out["CMP"] = rng.choice(pool)
    return out


def search(
    profile: str,
    *,
    iterations: int,
    seed: int,
    top: int,
    arches: tuple[str, ...] = ARCHITECTURES,
    use_pareto: bool = False,
) -> list[dict]:
    rng = random.Random(seed)
    best_cost: DecodeCost | None = None
    best_assign: dict[str, int] | None = None
    seen: set[tuple[tuple[str, int], ...]] = set()
    results: list[tuple[DecodeCost, dict[str, int]]] = []

    starts = [current_assignment(), random_assignment(rng)]
    for _ in range(max(4, iterations // 500)):
        starts.append(random_assignment(rng))

    temperature = 2.0
    cool = math.pow(0.01, 1.0 / max(iterations, 1))

    for start in starts:
        cur = dict(start)
        cur_cost = score_assignment(cur, profile)
        if cur_cost is None:
            continue
        for _step in range(iterations // len(starts)):
            nxt = neighbor(cur, rng)
            nxt_cost = score_assignment(nxt, profile)
            if nxt_cost is None:
                continue
            delta = nxt_cost.total - cur_cost.total
            if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-6)):
                cur, cur_cost = nxt, nxt_cost
            temperature *= cool

            key = tuple(sorted(cur.items()))
            if key not in seen:
                seen.add(key)
                results.append((cur_cost, dict(cur)))
                if best_cost is None or cur_cost.total < best_cost.total:
                    best_cost, best_assign = cur_cost, dict(cur)

    results.sort(key=lambda x: x[0].total)
    assignments = [assign for _cost, assign in results]
    if best_assign is not None and best_assign not in assignments:
        assignments.insert(0, best_assign)
    return _finalize_candidates(assignments, profile, top=top, arches=arches, use_pareto=use_pareto)


def search_lgc_direct(
    *,
    top: int,
    arches: tuple[str, ...] = ARCHITECTURES,
    use_pareto: bool = False,
    workers: int | None = None,
) -> list[dict]:
    """Exhaustive search over arithmetic opcode slots; logic opcodes fixed for direct lgc wire."""
    nworkers = max(1, workers if workers is not None else default_workers())
    evaluated = _run_lgc_direct_perms(arches=arches, use_pareto=use_pareto, workers=nworkers)
    evaluated.sort(key=lambda x: x[0])

    if use_pareto:
        assignments = _pareto_pool_from_evaluated(evaluated, arches)
        return _finalize_candidates(
            assignments,
            PROFILE_LGC_DIRECT,
            top=top,
            arches=arches,
            use_pareto=True,
            precomputed={
                assignment_key(assign): ac
                for _t, _c, assign, ac in evaluated
                if ac is not None
            },
        )

    seen: set[tuple[tuple[str, int], ...]] = set()
    assignments: list[dict[str, int]] = []
    for _total, _cost, assign, _ac in evaluated:
        key = tuple(sorted(assign.items()))
        if key in seen:
            continue
        seen.add(key)
        assignments.append(assign)
    return _finalize_candidates(
        assignments, PROFILE_LGC_DIRECT, top=top, arches=arches, use_pareto=False
    )


def _finalize_candidates(
    assignments: list[dict[str, int]],
    profile: str,
    *,
    top: int,
    arches: tuple[str, ...],
    use_pareto: bool,
    precomputed: dict[str, dict[str, ArchCost]] | None = None,
) -> list[dict]:
    if not use_pareto:
        unique: list[dict] = []
        for assign in assignments:
            if len(unique) >= top:
                break
            cand = candidate_dict(assign, profile, arches=arches)
            if cand not in unique:
                unique.append(cand)
        return unique[:top]

    entries: list[tuple[str, str, ArchCost]] = []
    assign_by_key: dict[str, dict[str, int]] = {}
    for assign in assignments:
        akey = assignment_key(assign)
        assign_by_key[akey] = assign
        if precomputed and akey in precomputed:
            arch_costs = precomputed[akey]
        else:
            try:
                rows, cmp_op = build_table(assign, profile)
            except ValueError:
                continue
            arch_costs = score_all_architectures(rows, profile, cmp_op=cmp_op, arches=arches)
        for arch in arches:
            entries.append((akey, arch, arch_costs[arch]))

    front = pareto_front(entries)

    ranked: list[tuple[tuple[int, int, int], str, str, dict]] = []
    for akey, arch, cost in front:
        assign = assign_by_key[akey]
        rank_key = cost.lex_key()
        cand = candidate_dict(assign, profile, arches=arches, recommended=arch, pareto_rank=1)
        ranked.append((rank_key, akey, arch, cand))

    ranked.sort(key=lambda x: x[0])

    unique_cands: list[dict] = []
    seen_assign: set[str] = set()
    for _rk, akey, _arch, cand in ranked:
        if akey in seen_assign:
            continue
        seen_assign.add(akey)
        unique_cands.append(cand)
        if len(unique_cands) >= top:
            break
    return unique_cands


def print_lgc_direct_table(assignment: dict[str, int]) -> None:
    rows, _ = build_table(assignment, PROFILE_LGC_DIRECT)
    inv: dict[int, list[str]] = {}
    for name, code in assignment.items():
        inv.setdefault(code, []).append(name)
    print("code | ops                     | cin bsel bcst | lgc3:0 (direct) | decode outs")
    print("-----+-------------------------+---------------+-----------------+------------")
    for op in range(16):
        names = ", ".join(inv.get(op, ["(free)"]))
        r = rows[op]
        lgc = "".join(str(r[f"net_lgc{i}"]) for i in range(3, -1, -1))
        lgc_d = "".join(str(x) for x in lgc_from_opcode_direct(op))
        print(
            f"  {op:02x} | {names:23s} | "
            f"{r['net_cin']}   {r['net_b_sel']}    {r['net_b_const_sel']}     | "
            f"{lgc_d:4s} ({lgc})      | "
            f"cin={r['net_cin']} bsel={r['net_b_sel']} bcst={r['net_b_const_sel']}"
        )


def print_arch_baseline(assignment: dict[str, int], profile: str, arches: tuple[str, ...]) -> None:
    rows, cmp_op = build_table(assignment, profile)
    costs = score_all_architectures(rows, profile, cmp_op=cmp_op, arches=arches)
    rec = recommend_arch(costs)
    print(f"  arch costs (profile={profile}, cmp_op={cmp_op}):")
    for arch in arches:
        c = costs[arch]
        feas = "" if c.feasible else " [infeasible]"
        print(
            f"    {arch:12s} dips={c.dips} adv={c.advanced_blocks} "
            f"gates={c.gates}{feas} parts={c.parts}"
        )
    print(f"    recommended: {rec}")


def print_baseline(arches: tuple[str, ...] = ARCHITECTURES) -> None:
    verify_signatures_match_cases()
    cur = current_assignment()
    print("=== Baseline (current opcode assignment) ===")
    legacy_rows = legacy_truth_table()
    gen = NetlistGen()
    gen_cost = gen.gate_count(legacy_rows, cmp_op=cur["CMP"])
    scored = legacy_gate_count(legacy_rows, cmp_op=cur["CMP"])
    print(f"NetlistGen legacy: {gen_cost}")
    print(f"score_truth_table legacy: {scored}")
    assert gen_cost == scored, f"mismatch {gen_cost} vs {scored}"

    for profile in PROFILES:
        if profile == PROFILE_LGC_DIRECT:
            continue
        cost = score_assignment(cur, profile)
        assert cost is not None
        print(f"  {profile}: {cost}")

    lgc_start = merge_lgc_direct(default_lgc_direct_arith())
    print(f"  {PROFILE_LGC_DIRECT} (default arith layout): {score_assignment(lgc_start, PROFILE_LGC_DIRECT)}")
    print(f"  logic opcodes (fixed): {lgc_direct_logic_assignment()}")
    print_arch_baseline(lgc_start, PROFILE_LGC_DIRECT, arches)
    print()


def _parse_arches(spec: str | None) -> tuple[str, ...]:
    if not spec:
        return ARCHITECTURES
    names = tuple(s.strip() for s in spec.split(",") if s.strip())
    for n in names:
        if n not in ARCHITECTURES:
            raise SystemExit(f"unknown arch {n!r}; choose from {ARCHITECTURES}")
    return names


def _print_pareto_candidate(i: int, cand: dict) -> None:
    c = cand["cost"]
    rec = cand.get("recommended_arch", ARCH_SOP)
    rc = cand["costs"].get(rec, {})
    print(
        f"  #{i} pareto rec={rec} dips={rc.get('dips')} adv={rc.get('advanced_blocks')} "
        f"gates={rc.get('gates')} sop_gates={c['total']} breaking={len(cand['breaking'])}"
    )
    if cand["notes"]:
        print(f"      {'; '.join(cand['notes'][:3])}")


def _print_sop_candidate(i: int, cand: dict) -> None:
    c = cand["cost"]
    print(
        f"  #{i} total={c['total']} ({c['n04']}x04 {c['n08']}x08 {c['n32']}x32) "
        f"breaking={len(cand['breaking'])}"
    )
    if cand["notes"]:
        print(f"      {'; '.join(cand['notes'][:3])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="append", choices=PROFILES, default=[PROFILE_LGC_DIRECT])
    parser.add_argument("--iter", type=int, default=20_000, help="search iterations per profile")
    parser.add_argument("--top", type=int, default=10, help="top candidates per profile")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json", type=Path, help="write ranked candidates JSON")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument(
        "--pareto",
        action="store_true",
        help="rank by multi-arch Pareto front (DIP, advanced blocks, gates)",
    )
    parser.add_argument(
        "--arch",
        default=None,
        help=f"comma-separated architectures (default: all): {','.join(ARCHITECTURES)}",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="parallel workers for exhaustive lgc_direct search (default: all CPU cores)",
    )
    args = parser.parse_args()
    arches = _parse_arches(args.arch)
    jobs = max(1, args.jobs) if args.jobs is not None else default_workers()

    print_baseline(arches)
    if args.baseline_only:
        return

    all_out: dict[str, list[dict]] = {}
    for profile in args.profile:
        print(f"=== Search profile={profile}" + (" pareto" if args.pareto else "") + " ===")
        if profile == PROFILE_LGC_DIRECT:
            found = search_lgc_direct(
                top=args.top, arches=arches, use_pareto=args.pareto, workers=jobs
            )
            print(
                f"  (exhaustive arithmetic placement; jobs={jobs}; "
                f"logic fixed at {dict(lgc_direct_logic_assignment())})"
            )
        else:
            print(f"  iter={args.iter}")
            found = search(
                profile,
                iterations=args.iter,
                seed=args.seed,
                top=args.top,
                arches=arches,
                use_pareto=args.pareto,
            )
        all_out[profile] = found
        printer = _print_pareto_candidate if args.pareto else _print_sop_candidate
        for i, cand in enumerate(found[:5], 1):
            printer(i, cand)
        if found and profile == PROFILE_LGC_DIRECT:
            print()
            print_lgc_direct_table({k: int(v) for k, v in found[0]["assignment"].items()})
        print()

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = {"pareto": args.pareto, "architectures": list(arches), "profiles": all_out}
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
