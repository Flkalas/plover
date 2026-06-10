"""Generate docs/hw-bringup/b3-opcode.md from shared ALU test vectors."""
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
        "INC/DEC: do **not** drive `net_b0..7`; use `153_B` sel (`b_const_sel`, `b_sel`) — see [alu8.md](../hw/netlist/blocks/alu8.md).",
        "",
        "## Control nets (quick ref)",
        "",
        "| Net | Role |",
        "|-----|------|",
        "| `net_cin` | 283 carry in (1 for SUB/CMP) |",
        "| `net_b_sel` | 153_B LSB: 0=B, 1=~B |",
        "| `net_b_const_sel` | 153_B MSB: 1 → INC/DEC constant mux |",
        "| `net_cmp_z`, `net_cmp_c_ge` | SUB-derived CMP flags (`Y==0`, `net_c_hi`) |",
        "| `net_153_s0/s1` | Logic enable → `157_YBP` selects `net_y_logic` |",
        "| `net_lgc0..3` | Gigatron 153 C0..C3 (from decode or DIP) |",
        "",
        "## 12 opcodes",
        "",
        "| sel | `alu_op` | Op | A | B | cin | b_sel | b_cst | s1 | s0 | lgc | b_hi | Y | Y LEDs y7..y0 | Fixed ties |",
        "|-----|----------|-----|---|---|-----|-------|-------|----|----|-----|------|---|---------------|------------|",
    ]

    for sel, (name, a, b, exp, c) in enumerate(CASES):
        lgc = f"{c['net_lgc3']}{c['net_lgc2']}{c['net_lgc1']}{c['net_lgc0']}"
        lines.append(
            f"| {sel} | `{sel:X}` | **{name}** | `{a:02X}` | `{b:02X}` | "
            f"{c['net_cin']} | {c['net_b_sel']} | {c['net_b_const_sel']} | "
            f"{c['net_153_s1']} | {c['net_153_s0']} | `{lgc}` | "
            f"{c['net_b_const_bit1']} | `{exp:02X}` | `{y_bits(exp)[::-1]}` | {fixed_ties(c)} |"
        )

    lines += [
        "",
        "Columns: **b_cst** = `net_b_const_sel`, **lgc** = `net_lgc3..0` (Gigatron C inputs), "
        "**b_hi** = `net_b_const_bit1..7` (same value), "
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
        "See phased bring-up: [M1-b3-procedure.md](M1-b3-procedure.md).",
        "",
    ]

    out = ROOT / "docs" / "hw-bringup" / "b3-opcode.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
