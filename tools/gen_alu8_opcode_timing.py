"""Generate hw/tests/alu8_opcode_timing.yaml — per-opcode Y path delay @ max."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import BCTRL_SUB, CASES, bits  # noqa: E402

SLOT = 600


def write_set(d: dict[str, int], indent: int = 6) -> list[str]:
    sp = " " * indent
    return [f"{sp}{k}: {d[k]}" for k in sorted(d.keys(), key=lambda x: (len(x), x))]


def _arith_path(name: str, c: dict[str, int]) -> list[str]:
    bctrl = tuple(c.get(f"net_bctrl{i}", 0) for i in range(4))
    if name in ("SUB", "CMP") or bctrl == BCTRL_SUB:
        return [
            "net_b0",
            "U_ALU_153_0.B",
            "U_ALU_153_0.2Y",
            "U_ALU_283_LO.B0",
            "U_ALU_283_LO.C4",
            "U_ALU_283_HI.C4",
            "U_ALU_157_YBP_0.1A",
            "U_ALU_157_YBP_0.1Y",
        ]
    if name == "INC" or (name == "ADD" and c.get("net_cin")):
        return [
            "net_cin",
            "U_ALU_283_LO.C0",
            "U_ALU_283_LO.C4",
            "U_ALU_283_HI.C4",
            "U_ALU_157_YBP_0.1A",
            "U_ALU_157_YBP_0.1Y",
        ]
    return [
        "U_ALU_283_LO.A0",
        "U_ALU_283_LO.C4",
        "U_ALU_283_HI.C4",
        "U_ALU_157_YBP_0.1A",
        "U_ALU_157_YBP_0.1Y",
    ]


def main() -> None:
    lines = [
        "netlist: ../netlist/blocks/alu8.yaml",
        "timing: max",
        f"duration_ns: {len(CASES) * SLOT}",
        "stimulus:",
    ]
    for i, (_name, a, b, _exp, c) in enumerate(CASES):
        s = {**bits("net_a", a), **bits("net_b", b), **c}
        lines.append(f"  - at_ns: {i * SLOT}")
        lines.append("    set:")
        lines.extend(write_set(s))

    lines.append("checks:")
    for i, (name, _a, _b, _exp, c) in enumerate(CASES):
        s0, s1 = c.get("net_153_s0", 0), c.get("net_153_s1", 0)
        if s0 or s1:
            path = [
                "U_ALU_153_0.A",
                "U_ALU_153_0.1Y",
                "U_ALU_157_YBP_0.4B",
                "U_ALU_157_YBP_0.4Y",
            ]
        else:
            path = _arith_path(name, c)
        lines += [
            f"  - type: slack",
            f"    label: {name}",
            f"    path: {path}",
            f"    budget_ns: 250",
            f"    min_slack_ns: 0",
        ]

    out = ROOT / "hw" / "tests" / "alu8_opcode_timing.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
