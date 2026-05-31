"""v0.2 alu_op[3:0] → ALU control nets + cmp_n (from alu8_cases)."""
from __future__ import annotations

from alu8_cases import CASES

# Maps alu8_cases ctrl() keys to ALU net names.
CTRL_NETS = [
    "net_sub_en",
    "net_cin",
    "net_153_s0",
    "net_153_s1",
    "net_b_sel",
    "net_c3_sel",
    "net_b_const_sel",
]

B_CONST_HI_KEY = "b_const_hi"  # drives net_b_const_bit1..7 together


def opcode_control(op: int) -> dict[str, int]:
    """Return control values for opcode 0..11; 12-15 treated as NOP."""
    if op >= len(CASES):
        return _nop_ctrl()
    _name, _a, _b, _y, c = CASES[op]
    out: dict[str, int] = {}
    for k in CTRL_NETS:
        out[k] = int(c.get(k, 0))
    hi = 0
    for i in range(1, 8):
        hi = int(c.get(f"net_b_const_bit{i}", 0))
        break
    out["b_const_hi"] = hi
    out["net_cmp_n"] = 0 if op == 11 else 1
    return out


def _nop_ctrl() -> dict[str, int]:
    return {
        **{k: 0 for k in CTRL_NETS},
        "b_const_hi": 0,
        "net_cmp_n": 1,
    }


def truth_table() -> list[dict[str, int]]:
    """16 rows (full 4-bit space)."""
    return [{**{"op": op}, **opcode_control(op)} for op in range(16)]


def op_bits(op: int) -> tuple[int, int, int, int]:
    return (op & 1, (op >> 1) & 1, (op >> 2) & 1, (op >> 3) & 1)


if __name__ == "__main__":
    for row in truth_table()[:12]:
        print(row)
