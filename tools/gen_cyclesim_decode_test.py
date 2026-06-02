"""Generate hw/tests/cyclesim/alu8_decode_full.yaml from alu8_cases."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES, bits  # noqa: E402


def op_bits(op: int) -> dict[str, int]:
    return {f"net_alu_op{i}": (op >> i) & 1 for i in range(4)}


def main() -> None:
    lines = [
        "netlist: ../../netlist/blocks/alu8_decode.yaml",
        "driver: stimulus",
        "stimulus:",
    ]
    for i, (_name, a, b, _exp, _c) in enumerate(CASES):
        s = {**bits("net_a", a), **bits("net_b", b), **op_bits(i)}
        lines.append(f"  - at_phase: {i}")
        lines.append("    set:")
        for k in sorted(s.keys(), key=lambda x: (len(x), x)):
            lines.append(f"      {k}: {s[k]}")

    lines.append("expect:")
    for i, (_name, _a, _b, exp, _c) in enumerate(CASES):
        lines.append(f"  - at_phase: {i}")
        for bit in range(8):
            lines.append(f"    net_y{bit}: {(exp >> bit) & 1}")
        if i == 11:
            lines.append("    net_cmp_z: 0")
            lines.append("    net_cmp_c_ge: 0")
        elif i == 2:
            lines.append("    net_cmp_z: 0")

    out = ROOT / "hw" / "tests" / "cyclesim" / "alu8_decode_full.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
