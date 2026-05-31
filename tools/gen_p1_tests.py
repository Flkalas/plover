"""Generate Phase1 integrated hwsim tests (cpu_datapath_p1)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES, bits  # noqa: E402

TESTS = ROOT / "hw" / "tests"
PERIOD = 500
CLK_LOW = 350
CLK_HIGH = 450
EXPECT_AFTER_CLK = 80


def op_bits(op: int) -> dict[str, int]:
    return {f"net_alu_op{i}": (op >> i) & 1 for i in range(4)}


def reg_bits(prefix: str, idx: int) -> dict[str, int]:
    return {f"{prefix}0": idx & 1, f"{prefix}1": (idx >> 1) & 1}


def _op(name: str) -> int:
    return next(i for i, (n, *_) in enumerate(CASES) if n == name)


def cw(op: int, src: int, dst: int) -> dict[str, int]:
    return {
        **op_bits(op),
        **reg_bits("net_src_reg", src),
        **reg_bits("net_dst_reg", dst),
        "net_bus_en0": 0,
        "net_bus_en1": 0,
    }


def inc_stimulus(reg: int, count: int, t0: int) -> list[str]:
    lines: list[str] = []
    op = _op("INC")
    for n in range(count):
        base = t0 + n * PERIOD
        lines.append(f"  - at_ns: {base}")
        lines.append("    set:")
        lines.append("      net_clk2: 0")
        for k, v in sorted(cw(op, reg, reg).items()):
            lines.append(f"      {k}: {v}")
        lines.append(f"  - at_ns: {base + CLK_LOW}")
        lines.append("    set:")
        lines.append("      net_clk2: 1")
        lines.append(f"  - at_ns: {base + CLK_HIGH}")
        lines.append("    set:")
        lines.append("      net_clk2: 0")
    return lines


def bit_expect(prefix: str, val: int) -> list[str]:
    return [f"    {prefix}{i}: {(val >> i) & 1}" for i in range(8)]


def write_add() -> None:
    add_op = _op("ADD")
    a_val, b_val, exp = 0x12, 0x34, 0x46
    t_init = 0
    t_add = PERIOD * (a_val + b_val + 2)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p1.yaml",
        "timing: max",
        f"duration_ns: {t_add + 400}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
    ]
    lines.extend(inc_stimulus(0, 0x12, t_init))
    lines.extend(inc_stimulus(2, 0x34, t_init + PERIOD * 0x12))
    lines.append(f"  - at_ns: {t_add}")
    lines.append("    set:")
    lines.append("      net_clk2: 0")
    for k, v in sorted(cw(add_op, 0, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {t_add + CLK_LOW}")
    lines.append("    set:")
    lines.append("      net_clk2: 1")
    lines.append("expect:")
    lines.append(f"  - at_ns: {t_add + CLK_LOW + EXPECT_AFTER_CLK}")
    lines.extend(bit_expect("net_r2_q", exp))
    for i in range(8):
        lines.append(f"    net_y{i}: {(exp >> i) & 1}")
    (TESTS / "p1_rmw_add.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p1_rmw_add.yaml")


def write_sub() -> None:
    sub_op = _op("SUB")
    a_val, b_val, exp = 0x12, 0x34, 0xDE
    t_init = 0
    t_sub = PERIOD * (0x12 + 0x34 + 2)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p1.yaml",
        "timing: max",
        f"duration_ns: {t_sub + 400}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
    ]
    lines.extend(inc_stimulus(0, a_val, t_init))
    lines.extend(inc_stimulus(2, b_val, t_init + PERIOD * a_val))
    lines.append(f"  - at_ns: {t_sub}")
    lines.append("    set:")
    lines.append("      net_clk2: 0")
    for k, v in sorted(cw(sub_op, 0, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {t_sub + CLK_LOW}")
    lines.append("    set:")
    lines.append("      net_clk2: 1")
    lines.append("expect:")
    lines.append(f"  - at_ns: {t_sub + CLK_LOW + EXPECT_AFTER_CLK}")
    lines.extend(bit_expect("net_r2_q", exp))
    lines.append("checks:")
    lines.append("  - type: slack")
    lines.append(
        "    path: [U_REG_R0.Q0, U_MUX_B_0.1C0, U_MUX_B_0.1Y, "
        "U_ALU_86_INV_0.A, U_ALU_86_INV_0.Y, U_ALU_157_B_0.1B, "
        "U_ALU_157_B_0.1Y, U_ALU_157_B2_0.1A, U_ALU_157_B2_0.1Y, "
        "U_ALU_283_LO.B0, U_ALU_283_LO.C4, U_ALU_283_HI.C4, "
        "U_ALU_153_0.1C0, U_ALU_153_0.1Y, U_REG_R2.D0, U_REG_R2.CP]"
    )
    lines.append("    budget_ns: 250")
    lines.append("    min_slack_ns: 0")
    (TESTS / "p1_rmw_sub.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p1_rmw_sub.yaml")


def write_cmp() -> None:
    cmp_op = _op("CMP")
    a_val, b_val, y_exp = 0x12, 0x34, 0xDE
    r2_before = b_val
    t_init = 0
    t_cmp = PERIOD * (a_val + b_val + 2)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p1.yaml",
        "timing: max",
        f"duration_ns: {t_cmp + 400}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
    ]
    lines.extend(inc_stimulus(0, a_val, t_init))
    lines.extend(inc_stimulus(2, b_val, t_init + PERIOD * a_val))
    lines.append(f"  - at_ns: {t_cmp}")
    lines.append("    set:")
    lines.append("      net_clk2: 0")
    for k, v in sorted(cw(cmp_op, 0, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {t_cmp + CLK_LOW}")
    lines.append("    set:")
    lines.append("      net_clk2: 1")
    lines.append("expect:")
    lines.append(f"  - at_ns: {t_cmp + CLK_LOW + EXPECT_AFTER_CLK}")
    for i in range(8):
        lines.append(f"    net_y{i}: {(y_exp >> i) & 1}")
    lines.append("    net_cmp_n: 0")
    lines.append(f"  - at_ns: {t_cmp + CLK_LOW + EXPECT_AFTER_CLK}")
    lines.extend(bit_expect("net_r2_q", r2_before))
    (TESTS / "p1_cmp_no_latch.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p1_cmp_no_latch.yaml")


def write_clock() -> None:
    add_op = _op("ADD")
    exp = 0x02
    cycle = 500
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p1_clock.yaml",
        "timing: max",
        "duration_ns: 2500",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
    ]
    inc_op = _op("INC")
    for k, v in sorted(cw(inc_op, 0, 0).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {cycle}")
    lines.append("    set:")
    for k, v in sorted(cw(inc_op, 2, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {cycle * 2}")
    lines.append("    set:")
    for k, v in sorted(cw(inc_op, 2, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append(f"  - at_ns: {cycle * 3}")
    lines.append("    set:")
    for k, v in sorted(cw(add_op, 0, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append("expect:")
    lines.append(f"  - at_ns: {cycle * 3 + 400}")
    lines.extend(bit_expect("net_r2_q", exp))
    lines.append("checks:")
    lines.append("  - type: frequency")
    lines.append("    signal: net_clk2")
    lines.append("    target_hz: 2000000")
    lines.append("    tolerance_pct: 5")
    lines.append("  - type: setup_hold")
    lines.append("  - type: slack")
    lines.append(
        "    path: [U_ALU_153_0.1Y, U_REG_R2.D0, U_REG_R2.CP, U_REG_R2.Q0]"
    )
    lines.append("    budget_ns: 250")
    lines.append("    min_slack_ns: 0")
    (TESTS / "p1_rmw_clock.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p1_rmw_clock.yaml")


def write_regfile_slack() -> None:
    sub_op = _op("SUB")
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p1.yaml",
        "timing: max",
        "duration_ns: 500",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
    ]
    for k, v in sorted(cw(sub_op, 0, 2).items()):
        lines.append(f"      {k}: {v}")
    lines.append("checks:")
    lines.append("  - type: slack")
    lines.append(
        "    path: [U_REG_R0.Q0, U_MUX_B_0.1C0, U_MUX_B_0.1Y, "
        "U_ALU_86_INV_0.A, U_ALU_86_INV_0.Y, U_ALU_157_B_0.1B, "
        "U_ALU_157_B_0.1Y, U_ALU_157_B2_0.1A, U_ALU_157_B2_0.1Y, "
        "U_ALU_283_LO.B0, U_ALU_283_LO.C4, U_ALU_283_HI.C4, "
        "U_ALU_153_0.1C0, U_ALU_153_0.1Y]"
    )
    lines.append("    budget_ns: 250")
    lines.append("    min_slack_ns: 0")
    lines.append("  - type: slack")
    lines.append(
        "    path: [U_REG_R0.Q0, U_MUX_B_0.1C0, U_MUX_B_0.1Y, "
        "U_ALU_86_INV_0.A, U_ALU_86_INV_0.Y, U_ALU_157_B_0.1B, "
        "U_ALU_157_B_0.1Y, U_ALU_157_B2_0.1A, U_ALU_157_B2_0.1Y, "
        "U_ALU_283_LO.B0, U_ALU_283_LO.C4, U_ALU_283_HI.C4, "
        "U_ALU_153_0.1C0, U_ALU_153_0.1Y, U_REG_R2.D0, U_REG_R2.CP]"
    )
    lines.append("    budget_ns: 250")
    lines.append("    min_slack_ns: 0")
    (TESTS / "regfile_rmw_4x153_slack.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote regfile_rmw_4x153_slack.yaml")


def main() -> None:
    write_add()
    write_sub()
    write_cmp()
    write_clock()
    write_regfile_slack()


if __name__ == "__main__":
    main()
