#!/usr/bin/env python3
"""Cumulative software-stack regression gate (--through Sn)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MILESTONES: dict[str, list[str]] = {
    "S0": [],
    "S1": ["tests/test_plover_asm.py"],
    "S2": ["tests/test_plover_asm.py", "tests/test_add_imm.py", "tests/test_call_ret.py"],
    "S3": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
    ],
    "S3c": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_normative.py",
    ],
    "S4": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
    ],
    "S5": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
    ],
    "S6": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
        "tests/test_kernel_boot.py",
    ],
    "S7a": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
        "tests/test_kernel_boot.py",
        "tests/test_vfdd_io.py",
    ],
    "S7b": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
        "tests/test_kernel_boot.py",
        "tests/test_vfdd_io.py",
        "tests/test_fat_fs.py",
    ],
    "S7c": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
        "tests/test_kernel_boot.py",
        "tests/test_vfdd_io.py",
        "tests/test_fat_fs.py",
        "tests/test_plr_exec.py",
    ],
    "S7d": [
        "tests/test_plover_asm.py",
        "tests/test_add_imm.py",
        "tests/test_call_ret.py",
        "tests/test_forth_primitives.py",
        "tests/test_forth_interpret.py",
        "tests/test_forth_blocks.py",
        "tests/test_plover_cc.py",
        "tests/test_plover_cc_obj.py",
        "tests/test_plover_asm_obj.py",
        "tests/test_linker_resolve.py",
        "tests/test_linker_reloc.py",
        "tests/test_kernel_boot.py",
        "tests/test_vfdd_io.py",
        "tests/test_fat_fs.py",
        "tests/test_plr_exec.py",
        "tests/test_dos_shell.py",
    ],
}

SCENARIOS: dict[str, list[str]] = {
    "S3": ["hw/scenarios/vm/forth_boot.yaml"],
    "S6": ["hw/scenarios/vm/forth_boot.yaml", "hw/scenarios/vm/os_boot.yaml"],
    "S7d": [
        "hw/scenarios/vm/forth_boot.yaml",
        "hw/scenarios/vm/os_boot.yaml",
        "hw/scenarios/vm/dos_boot.yaml",
    ],
}


def _ordered_through(name: str) -> list[str]:
    order = ["S0", "S1", "S2", "S3", "S3c", "S4", "S5", "S6", "S7a", "S7b", "S7c", "S7d"]
    if name not in order:
        raise SystemExit(f"unknown milestone: {name}")
    idx = order.index(name)
    tests: list[str] = []
    seen: set[str] = set()
    for m in order[: idx + 1]:
        for t in MILESTONES.get(m, []):
            if t not in seen:
                seen.add(t)
                tests.append(t)
    return tests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--through", default="S7d", help="Milestone gate (S0..S7d)")
    ap.add_argument("--skip-scenarios", action="store_true")
    args = ap.parse_args()

    tests = _ordered_through(args.through)
    if tests:
        cmd = [sys.executable, "-m", "pytest", "-q", *tests]
        print("RUN", " ".join(cmd))
        if subprocess.run(cmd, cwd=ROOT).returncode != 0:
            return 1
    else:
        cmd = [sys.executable, "-m", "pytest", "-q", "tests/test_add_imm.py"]
        if subprocess.run(cmd, cwd=ROOT).returncode != 0:
            return 1

    if not args.skip_scenarios:
        for scen in SCENARIOS.get(args.through, []):
            path = ROOT / scen
            if not path.is_file():
                print(f"SKIP missing scenario {scen}")
                continue
            cmd = [sys.executable, "-m", "plover_vm", "scenario", str(path)]
            print("RUN", " ".join(cmd))
            if subprocess.run(cmd, cwd=ROOT).returncode != 0:
                return 1

    print(f"PASS through {args.through}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
