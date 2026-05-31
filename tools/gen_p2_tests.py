"""Generate Phase2 hwsim tests (ROM CW supply)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES  # noqa: E402
from pack_rom import cw_add, cw_inc, pack_cw, pack_imm_literal  # noqa: E402

TESTS = ROOT / "hw" / "tests"
PERIOD = 500
CLK_LOW = 350
CLK_HIGH = 450
EXPECT_AFTER_CLK = 80


def _op(name: str) -> int:
    return next(i for i, (n, *_) in enumerate(CASES) if n == name)


def bit_expect(prefix: str, val: int) -> list[str]:
    return [f"    {prefix}{i}: {(val >> i) & 1}" for i in range(8)]


def cw_bits(word: int) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in range(4):
        out[f"net_alu_op{i}"] = (word >> (12 + i)) & 1
    for i in range(2):
        out[f"net_src_reg{i}"] = (word >> (10 + i)) & 1
        out[f"net_dst_reg{i}"] = (word >> (8 + i)) & 1
        out[f"net_bus_en{i}"] = (word >> (6 + i)) & 1
    for i in range(6):
        out[f"net_ctrl{i}"] = (word >> i) & 1
    return out


def clk_stimulus_manual(cycles: int, t0: int = 0) -> list[str]:
    lines: list[str] = []
    for n in range(cycles):
        base = t0 + n * PERIOD
        lines += [
            f"  - at_ns: {base}",
            "    set:",
            "      net_clk2: 0",
            f"  - at_ns: {base + CLK_LOW}",
            "    set:",
            "      net_clk2: 1",
            f"  - at_ns: {base + CLK_HIGH}",
            "    set:",
            "      net_clk2: 0",
        ]
    return lines


def write_rom_fetch_word() -> None:
    word = cw_add(0, 2)
    bits = cw_bits(word)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p2.yaml",
        "timing: max",
        "duration_ns: 200",
        f"rom_image:",
        f"  - {word:#06x}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
        "      net_pc0: 0",
        "      net_pc1: 0",
        "      net_pc2: 0",
        "      net_pc3: 0",
        "      net_pc4: 0",
        "      net_pc5: 0",
        "      net_pc6: 0",
        "      net_pc7: 0",
        "expect:",
        "  - at_ns: 80",
    ]
    for net, val in sorted(bits.items()):
        lines.append(f"    {net}: {val}")
    (TESTS / "rom_fetch_word.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote rom_fetch_word.yaml")


def write_p2_rom_rmw_add() -> None:
    n_inc0 = 0x12
    n_inc2 = 0x34
    n_words = n_inc0 + n_inc2 + 1
    duration = n_words * PERIOD + 400
    expect_at = (n_words - 1) * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    exp = 0x46
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p2.yaml",
        "timing: max",
        f"duration_ns: {duration}",
        "rom_image_file: ../fixtures/rom/rmw_add/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
    ]
    for c in range(n_words):
        base = c * PERIOD
        lines.append(f"  - at_ns: {base}")
        lines.append("    set:")
        for i in range(8):
            lines.append(f"      net_pc{i}: {(c >> i) & 1}")
        lines += [
            f"  - at_ns: {base + CLK_LOW}",
            "    set:",
            "      net_clk2: 1",
            f"  - at_ns: {base + CLK_HIGH}",
            "    set:",
            "      net_clk2: 0",
        ]
    lines += [
        "expect:",
        f"  - at_ns: {expect_at}",
    ]
    lines.extend(bit_expect("net_r2_q", exp))
    for i in range(8):
        lines.append(f"    net_y{i}: {(exp >> i) & 1}")
    (TESTS / "p2_rom_rmw_add.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p2_rom_rmw_add.yaml")


def write_p2_rom_program() -> None:
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p2_clock.yaml",
        "timing: max",
        "duration_ns: 2500",
        "rom_image_file: ../fixtures/rom/clock_add_demo/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
        "expect:",
        "  - at_ns: 1900",
    ]
    lines.extend(bit_expect("net_r2_q", 0x02))
    lines += [
        "checks:",
        "  - type: frequency",
        "    signal: net_clk2",
        "    target_hz: 2000000",
        "    tolerance_pct: 5",
        "  - type: setup_hold",
        "  - type: slack",
        "    path: [U_ROM.D12, U_DEC_04_1.A, U_DEC_04_1.Y, U_ALU_153_0.1Y, U_REG_R2.D0, U_REG_R2.CP, U_REG_R2.Q0]",
        "    budget_ns: 250",
        "    min_slack_ns: 0",
    ]
    (TESTS / "p2_rom_program.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p2_rom_program.yaml")


def write_p2_imm_load() -> None:
    word = pack_imm_literal(0xA5)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p2.yaml",
        "timing: max",
        "duration_ns: 500",
        f"rom_image:",
        f"  - {word:#06x}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
        "      net_pc0: 0",
        "      net_pc1: 0",
        "      net_pc2: 0",
        "      net_pc3: 0",
        "      net_pc4: 0",
        "      net_pc5: 0",
        "      net_pc6: 0",
        "      net_pc7: 0",
        f"  - at_ns: {CLK_LOW}",
        "    set:",
        "      net_clk2: 1",
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
    ]
    lines.extend(bit_expect("net_r2_q", 0xA5))
    (TESTS / "p2_imm_load.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p2_imm_load.yaml")


def write_rom_fetch_timing() -> None:
    word = cw_add(0, 2)
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p2.yaml",
        "timing: max",
        "duration_ns: 500",
        f"rom_image:",
        f"  - {word:#06x}",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_cmp_n: 1",
        "      net_pc0: 0",
        "      net_pc1: 0",
        "      net_pc2: 0",
        "      net_pc3: 0",
        "      net_pc4: 0",
        "      net_pc5: 0",
        "      net_pc6: 0",
        "      net_pc7: 0",
        f"  - at_ns: {CLK_LOW}",
        "    set:",
        "      net_clk2: 1",
        "checks:",
        "  - type: slack",
        "    path: [U_ROM.D12, U_DEC_04_1.A, U_DEC_04_1.Y, U_DEC_08_1.A, U_DEC_08_1.Y, "
        "U_MUX_B_0.1C0, U_MUX_B_0.1Y, U_IMM_B_MUX_0.1A, U_IMM_B_MUX_0.1Y, "
        "U_ALU_86_INV_0.A, U_ALU_86_INV_0.Y, U_ALU_157_B_0.1B, U_ALU_157_B_0.1Y, "
        "U_ALU_283_LO.B0, U_ALU_283_LO.C4, U_ALU_153_0.1Y]",
        "    budget_ns: 250",
        "    min_slack_ns: 0",
        "  - type: path_delay",
        "    from_net: net_pc0",
        "    to_net: net_y0",
        "    after_ns: 0",
        "    max_delay_ns: 250",
    ]
    (TESTS / "rom_fetch_timing.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote rom_fetch_timing.yaml")


def main() -> None:
    write_rom_fetch_word()
    write_p2_rom_rmw_add()
    write_p2_rom_program()
    write_p2_imm_load()
    write_rom_fetch_timing()


if __name__ == "__main__":
    main()
