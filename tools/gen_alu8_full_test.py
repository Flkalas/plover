"""Generate hw/tests/alu8_full.yaml with 157 B2 cascade controls."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES, bits  # noqa: E402

SLOT = 600


def write_set(d: dict[str, int], indent: int = 6) -> list[str]:
    sp = " " * indent
    return [f"{sp}{k}: {d[k]}" for k in sorted(d.keys(), key=lambda x: (len(x), x))]


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

    lines.append("expect:")
    for i, (_name, _a, _b, exp, _c) in enumerate(CASES):
        lines.append(f"  - at_ns: {i * SLOT + 400}")
        for bit in range(8):
            lines.append(f"    net_y{bit}: {(exp >> bit) & 1}")

    out = ROOT / "hw" / "tests" / "alu8_full.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
