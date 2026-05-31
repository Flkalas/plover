"""Generate docs/hw-bringup-b3-opcode.md from shared ALU test vectors."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES  # noqa: E402


def y_bits(exp: int) -> str:
    return "".join(str((exp >> i) & 1) for i in range(8))


def fixed_ties(c: dict[str, int]) -> str:
    zeros = [k.replace("net_", "") for k, v in c.items() if v == 0]
    ones = [k.replace("net_", "") for k, v in c.items() if v == 1]
    parts: list[str] = []
    if zeros:
        parts.append("GND: " + ", ".join(zeros))
    if ones:
        parts.append("VCC: " + ", ".join(ones))
    return "; ".join(parts) if parts else "—"


def main() -> None:
    lines = [
        "# B3 — opcode → control line cheat sheet",
        "",
        "Breadboard **DIP / tie** settings for 12 `alu_op[3:0]` operations (v0.2 CW `[15:12]`). "
        "Generated from the same vectors as [`alu8_full.yaml`](../hw/tests/alu8_full.yaml).",
        "",
        "Regenerate: `python tools/gen_opcode_cheatsheet.py`",
        "",
        "**Netlist has no `alu_sel` bus** — in Phase1 hwsim use [`alu_decode.yaml`](../hw/netlist/blocks/alu_decode.yaml) "
        "or set each control net manually (or hardwire per row).",
        "",
        "INC/DEC: do **not** drive `net_b0..7`; use `b_const_sel` + `b_const_bit1..7` only.",
        "",
        "## Control nets (quick ref)",
        "",
        "| Net | Role |",
        "|-----|------|",
        "| `net_sub_en` | 1 → invert B (SUB/CMP) |",
        "| `net_cin` | 283 carry in (1 for SUB/CMP) |",
        "| `net_b_sel` | 157 stage-1: 0=B, 1=~B |",
        "| `net_b_const_sel` | 157 B2: 0=path, 1=INC/DEC constant |",
        "| `net_b_const_bit1..7` | INC=0, DEC=1 (bit0 = VCC in netlist) |",
        "| `net_153_s0/s1` | Output MUX: 00=sum, 01=and, 10=or, 11=C3 |",
        "| `net_c3_sel` | 157 OUT: 0=XOR path, 1=~A (NOT) |",
        "",
        "## 12 opcodes",
        "",
        "| sel | `alu_op` | Op | A | B | sub | cin | b_sel | b_cst | s1 | s0 | c3 | b_hi | Y | Y LEDs y7..y0 | Fixed ties |",
        "|-----|----------|-----|---|---|-----|-----|-------|-------|----|----|----|------|---|---------------|------------|",
    ]

    for sel, (name, a, b, exp, c) in enumerate(CASES):
        lines.append(
            f"| {sel} | `{sel:X}` | **{name}** | `{a:02X}` | `{b:02X}` | "
            f"{c['net_sub_en']} | {c['net_cin']} | {c['net_b_sel']} | {c['net_b_const_sel']} | "
            f"{c['net_153_s1']} | {c['net_153_s0']} | {c['net_c3_sel']} | "
            f"{c['net_b_const_bit1']} | `{exp:02X}` | `{y_bits(exp)[::-1]}` | {fixed_ties(c)} |"
        )

    lines += [
        "",
        "Columns: **b_cst** = `net_b_const_sel`, **b_hi** = `net_b_const_bit1..7` (same value), "
        "**Y LEDs** = MSB left (y7) … LSB (y0).",
        "",
        "## Smoke vectors (B3a first)",
        "",
        "| Op | A | B | Expected Y |",
        "|----|---|---|------------|",
        "| SUB | 0x12 | 0x34 | 0xDE |",
        "| XOR | 0x12 | 0x34 | 0x26 |",
        "| INC | 0x12 | — | 0x13 |",
        "",
        "See phased bring-up: [hw-bringup-b3.md](hw-bringup-b3.md).",
        "",
    ]

    out = ROOT / "docs" / "hw-bringup-b3-opcode.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
