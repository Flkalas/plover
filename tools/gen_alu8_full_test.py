"""Generate hw/tests/alu8_full.yaml with 157 B2 cascade controls."""
from __future__ import annotations

from pathlib import Path


def bits(prefix: str, val: int) -> dict[str, int]:
    return {f"{prefix}{i}": (val >> i) & 1 for i in range(8)}


def ctrl(
    sub: int = 0,
    cin: int = 0,
    s0: int = 0,
    s1: int = 0,
    b_sel: int = 0,
    c3_sel: int = 0,
    b_const_sel: int = 0,
    b_const_hi: int = 0,
) -> dict[str, int]:
    out = {
        "net_sub_en": sub,
        "net_cin": cin,
        "net_153_s0": s0,
        "net_153_s1": s1,
        "net_b_sel": b_sel,
        "net_c3_sel": c3_sel,
        "net_b_const_sel": b_const_sel,
    }
    for i in range(1, 8):
        out[f"net_b_const_bit{i}"] = b_const_hi
    return out


def write_set(d: dict[str, int], indent: int = 6) -> list[str]:
    sp = " " * indent
    return [f"{sp}{k}: {d[k]}" for k in sorted(d.keys(), key=lambda x: (len(x), x))]


CASES = [
    ("NOP", 0x00, 0x00, 0x00, ctrl()),
    ("ADD", 0x12, 0x34, 0x46, ctrl()),
    ("SUB", 0x12, 0x34, 0xDE, ctrl(sub=1, cin=1, b_sel=1)),
    ("AND", 0x12, 0x34, 0x10, ctrl(s0=1)),
    ("OR", 0x12, 0x34, 0x36, ctrl(s1=1)),
    ("XOR", 0x12, 0x34, 0x26, ctrl(s0=1, s1=1)),
    ("NOT", 0x12, 0x00, 0xED, ctrl(s0=1, s1=1, c3_sel=1)),
    ("PASS_A", 0x12, 0xFF, 0x12, ctrl(s0=1)),
    ("PASS_B", 0xFF, 0x34, 0x34, ctrl(s0=1)),
    ("INC", 0x12, 0x00, 0x13, ctrl(b_const_sel=1, b_const_hi=0)),
    ("DEC", 0x12, 0x00, 0x11, ctrl(b_const_sel=1, b_const_hi=1)),
    ("CMP", 0x12, 0x34, 0xDE, ctrl(sub=1, cin=1, b_sel=1)),
]

SLOT = 600


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

    out = Path(__file__).resolve().parents[1] / "hw" / "tests" / "alu8_full.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
