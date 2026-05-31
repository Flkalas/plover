"""Generate Phase3 hwsim tests (LOCAL ctrl, flags, PC/branch)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES  # noqa: E402
from pack_rom import (  # noqa: E402
    cw_add,
    cw_beq,
    cw_cmp_flg,
    cw_inc,
    cw_jmp,
    cw_local_nop,
    pack_cw,
    pack_local_ctrl,
)

TESTS = ROOT / "hw" / "tests"
BLOCKS = ROOT / "hw" / "netlist" / "blocks"
PERIOD = 500
CLK_LOW = 350
CLK_HIGH = 450
EXPECT_AFTER_CLK = 80


def _split(text: str) -> tuple[str, str]:
    _, rest = text.split("instances:", 1)
    inst, nets = rest.split("nets:", 1)
    return inst, nets


def merge_blocks(paths: list[Path], name: str, out: Path) -> None:
    inst_parts: list[str] = []
    net_parts: list[str] = []
    for path in paths:
        inst, nets = _split(path.read_text(encoding="utf-8"))
        inst_parts.append(inst)
        net_parts.append(nets)
    text = (
        f"version: 1\nblock: {name}\ninstances:"
        + "".join(inst_parts)
        + "nets:"
        + "".join(net_parts)
    )
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


def _op(name: str) -> int:
    return next(i for i, (n, *_) in enumerate(CASES) if n == name)


def bit_expect(prefix: str, val: int, width: int = 8) -> list[str]:
    return [f"    {prefix}{i}: {(val >> i) & 1}" for i in range(width)]


def set_bits(prefix: str, val: int, width: int = 8) -> list[str]:
    return [f"      {prefix}{i}: {(val >> i) & 1}" for i in range(width)]


def clk_cycle(base: int) -> list[str]:
    return [
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


def ctrl_set(**bits: int) -> list[str]:
    lines = ["    set:"]
    for i in range(6):
        if f"c{i}" in bits or f"ctrl{i}" in bits:
            val = bits.get(f"c{i}", bits.get(f"ctrl{i}", 0))
            lines.append(f"      net_ctrl{i}: {val}")
    if "bus0" in bits:
        lines.append(f"      net_bus_en0: {bits['bus0']}")
    if "bus1" in bits:
        lines.append(f"      net_bus_en1: {bits['bus1']}")
    if "z_prev" in bits:
        lines.append(f"      net_z_prev: {bits['z_prev']}")
    return lines


def write_pc_local_block() -> None:
    merge_blocks(
        [BLOCKS / "local_ctrl.yaml", BLOCKS / "pc.yaml"],
        "pc_local",
        BLOCKS / "pc_local.yaml",
    )


def write_local_ctrl_decode() -> None:
    lines = [
        "netlist: ../netlist/blocks/local_ctrl.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl0: 0",
        "      net_ctrl1: 0",
        "      net_ctrl2: 1",
        "      net_ctrl3: 0",
        "      net_ctrl4: 0",
        "      net_ctrl5: 0",
        "      net_z_prev: 0",
        "expect:",
        "  - at_ns: 500",
        "    net_local_en: 1",
        "    net_pc_count_en: 1",
        "    net_pc_load: 0",
        "    net_flg_we: 0",
        "    net_halt: 0",
    ]
    (TESTS / "local_ctrl_decode.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote local_ctrl_decode.yaml")


def write_local_ctrl_priority() -> None:
    lines = [
        "netlist: ../netlist/blocks/local_ctrl.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl0: 0",
        "      net_ctrl1: 1",
        "      net_ctrl2: 1",
        "      net_ctrl3: 1",
        "      net_ctrl4: 1",
        "      net_ctrl5: 1",
        "      net_z_prev: 1",
        "expect:",
        "  - at_ns: 250",
        "    net_halt: 1",
        "    net_pc_count_en: 0",
        "    net_pc_load: 0",
        "    net_flg_we: 0",
    ]
    (TESTS / "local_ctrl_priority.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote local_ctrl_priority.yaml")


def write_pc_inc() -> None:
    lines = [
        "netlist: ../netlist/blocks/pc_local.yaml",
        "timing: max",
        "duration_ns: 1200",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl0: 0",
        "      net_ctrl1: 0",
        "      net_ctrl2: 1",
        "      net_ctrl3: 0",
        "      net_ctrl4: 0",
        "      net_ctrl5: 0",
        "      net_z_prev: 0",
    ]
    for c in range(2):
        base = c * PERIOD
        lines += clk_cycle(base)
        if c == 1:
            lines += [
                f"  - at_ns: {base}",
                "    set:",
                "      net_ctrl2: 1",
            ]
    lines += [
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
    ]
    lines.extend(bit_expect("net_pc", 1, 16))
    lines += [
        f"  - at_ns: {2 * PERIOD + CLK_LOW + EXPECT_AFTER_CLK}",
    ]
    lines.extend(bit_expect("net_pc", 2, 16))
    (TESTS / "pc_inc.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote pc_inc.yaml")


def write_pc_hold() -> None:
    lines = [
        "netlist: ../netlist/blocks/pc_local.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl2: 0",
        "      net_z_prev: 0",
    ]
    lines += clk_cycle(0)
    lines += [
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
    ]
    lines.extend(bit_expect("net_pc", 0, 16))
    (TESTS / "pc_hold.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote pc_hold.yaml")


def write_pc_jump() -> None:
    target = 0x1234
    lines = [
        "netlist: ../netlist/blocks/pc_local.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl4: 0",
        "      net_ctrl5: 1",
        "      net_z_prev: 0",
    ]
    lines.extend(set_bits("net_r0_q", target & 0xFF))
    lines.extend(set_bits("net_r1_q", (target >> 8) & 0xFF))
    lines += clk_cycle(0)
    lines += [
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
    ]
    lines.extend(bit_expect("net_pc", target, 16))
    (TESTS / "pc_jump.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote pc_jump.yaml")


def write_pc_branch_beq() -> None:
    target = 0x0056
    lines = [
        "netlist: ../netlist/blocks/pc_local.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl4: 1",
        "      net_ctrl5: 0",
        "      net_z_prev: 1",
    ]
    lines.extend(set_bits("net_r0_q", target & 0xFF))
    lines.extend(set_bits("net_r1_q", (target >> 8) & 0xFF))
    lines += clk_cycle(0)
    lines += ["expect:", f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}"]
    lines.extend(bit_expect("net_pc", target, 16))
    (TESTS / "pc_branch_beq.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote pc_branch_beq.yaml")

    lines = [
        "netlist: ../netlist/blocks/pc_local.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_bus_en0: 0",
        "      net_bus_en1: 0",
        "      net_ctrl4: 1",
        "      net_ctrl5: 1",
        "      net_z_prev: 0",
    ]
    lines.extend(set_bits("net_r0_q", target & 0xFF))
    lines.extend(set_bits("net_r1_q", (target >> 8) & 0xFF))
    lines += clk_cycle(0)
    lines += ["expect:", f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}"]
    lines.extend(bit_expect("net_pc", target, 16))
    (TESTS / "pc_branch_bne.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote pc_branch_bne.yaml")


def write_flg_we_cmp() -> None:
    lines = [
        "netlist: ../netlist/blocks/flg_latch.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_flg_we: 1",
        "      net_c_hi: 0",
    ]
    lines.extend(bit_expect("net_y", 0))
    lines += clk_cycle(0)
    lines += [
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
        "    net_z_flg: 1",
        "    net_z_prev: 1",
    ]
    (TESTS / "flg_we_cmp.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote flg_we_cmp.yaml")


def write_flg_we_sub() -> None:
    lines = [
        "netlist: ../netlist/blocks/flg_latch.yaml",
        "timing: max",
        "duration_ns: 600",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_clk2: 0",
        "      net_flg_we: 1",
        "      net_c_hi: 1",
    ]
    lines.extend(bit_expect("net_y", 7))
    lines += clk_cycle(0)
    lines += [
        "expect:",
        f"  - at_ns: {CLK_LOW + EXPECT_AFTER_CLK}",
        "    net_c_flg: 1",
    ]
    (TESTS / "flg_we_sub.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote flg_we_sub.yaml")


def write_cmp_flg_we() -> None:
    """ROM program: equal CMP + FLG_WE sets Z_flg (word index 6)."""
    cmp_idx = 6
    cmp_expect = cmp_idx * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    n_words = 13
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p3.yaml",
        "timing: max",
        f"duration_ns: {n_words * PERIOD + 400}",
        "rom_image_file: ../fixtures/rom/branch_slot/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
    ]
    for c in range(n_words):
        lines += clk_cycle(c * PERIOD)
    lines += [
        "expect:",
        f"  - at_ns: {cmp_expect}",
        "    net_z_flg: 1",
    ]
    (TESTS / "cmp_flg_we.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote cmp_flg_we.yaml")


def write_p3_branch_slot() -> None:
    cmp_idx = 6
    beq_idx = 10
    z_expect = cmp_idx * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    beq_expect = beq_idx * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    n_words = 13
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p3.yaml",
        "timing: max",
        f"duration_ns: {n_words * PERIOD + 400}",
        "rom_image_file: ../fixtures/rom/branch_slot/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
    ]
    for c in range(n_words):
        lines += clk_cycle(c * PERIOD)
    lines += [
        "expect:",
        f"  - at_ns: {z_expect}",
        "    net_z_prev: 1",
        f"  - at_ns: {beq_expect}",
    ]
    lines.extend(bit_expect("net_pc", 3, 16))
    (TESTS / "p3_branch_slot.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p3_branch_slot.yaml")


def write_p3_rom_branch_demo() -> None:
    beq_idx = 10
    beq_expect = beq_idx * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    n_words = 13
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p3.yaml",
        "timing: max",
        f"duration_ns: {n_words * PERIOD + 400}",
        "rom_image_file: ../fixtures/rom/branch_slot/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
    ]
    for c in range(n_words):
        lines += clk_cycle(c * PERIOD)
    lines += [
        "expect:",
        f"  - at_ns: {beq_expect}",
    ]
    lines.extend(bit_expect("net_pc", 3, 16))
    (TESTS / "p3_rom_branch_demo.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p3_rom_branch_demo.yaml")


def write_p3_pc_sequential() -> None:
    n_words = 3
    expect_at = (n_words - 1) * PERIOD + CLK_LOW + EXPECT_AFTER_CLK
    lines = [
        "netlist: ../netlist/blocks/cpu_datapath_p3.yaml",
        "timing: max",
        f"duration_ns: {n_words * PERIOD + 400}",
        "rom_image_file: ../fixtures/rom/p3_clock_add/rom_words.hex",
        "stimulus:",
        "  - at_ns: 0",
        "    set:",
        "      net_cmp_n: 1",
    ]
    for c in range(n_words):
        lines += clk_cycle(c * PERIOD)
    lines += [
        "expect:",
        f"  - at_ns: {expect_at}",
    ]
    lines.extend(bit_expect("net_r2_q", 0x02))
    (TESTS / "p3_pc_sequential.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote p3_pc_sequential.yaml")


def main() -> None:
    write_pc_local_block()
    write_local_ctrl_decode()
    write_local_ctrl_priority()
    write_pc_inc()
    write_pc_hold()
    write_pc_jump()
    write_pc_branch_beq()
    write_flg_we_cmp()
    write_flg_we_sub()
    write_cmp_flg_we()
    write_p3_branch_slot()
    write_p3_rom_branch_demo()
    write_p3_pc_sequential()


if __name__ == "__main__":
    main()
