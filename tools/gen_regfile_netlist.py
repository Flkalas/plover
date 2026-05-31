"""Generate hw/netlist/blocks/regfile.yaml — 4x574 + 8x153 + CP decode."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "hw" / "netlist" / "blocks" / "regfile.yaml"


def reg574(ref: str, idx: int) -> list[str]:
    lines = [f"  - ref: {ref}", "    part: 74HC574", "    pins:"]
    for i in range(8):
        lines.append(f"      D{i}: net_y{i}")
        lines.append(f"      Q{i}: net_r{idx}_q{i}")
    lines += [
        f"      CP: net_cp_r{idx}",
        "      OE: pwr_gnd",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    return lines


def mux153_pair(ref: str, port: str, bit_lo: int) -> list[str]:
    sel0 = "net_src_reg0" if port == "a" else "net_dst_reg0"
    sel1 = "net_src_reg1" if port == "a" else "net_dst_reg1"
    y0 = f"net_{port}{bit_lo}" if port == "a" else f"net_b153_{bit_lo}"
    y1 = f"net_{port}{bit_lo + 1}" if port == "a" else f"net_b153_{bit_lo + 1}"
    lines = [f"  - ref: {ref}", "    part: 74HC153", "    pins:"]
    for i in range(4):
        lines.append(f"      1C{i}: net_r{i}_q{bit_lo}")
        lines.append(f"      2C{i}: net_r{i}_q{bit_lo + 1}")
    lines += [
        f"      1Y: {y0}",
        f"      2Y: {y1}",
        "      1G: pwr_gnd",
        "      2G: pwr_gnd",
        f"      A: {sel0}",
        f"      B: {sel1}",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    return lines


def imm_b_mux(bit: int) -> list[str]:
    imm_net = f"net_ctrl{bit}" if bit < 6 else f"net_dst_reg{bit - 6}"
    return [
        f"  - ref: U_IMM_B_MUX_{bit}",
        "    part: 74HC157",
        "    pins:",
        f"      1A: net_b153_{bit}",
        f"      1B: {imm_net}",
        f"      1Y: net_b{bit}",
        "      S: net_bus_imm",
        "      OE: pwr_gnd",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]


def cp_gate(idx: int, *, halt_mask: bool) -> list[str]:
    inv_y = f"net_cp_inv_r{idx}"
    and1 = f"net_cp_en_r{idx}"
    pre = f"net_cp_pre_r{idx}"
    lines = [
        f"  - ref: U_CP_INV_{idx}",
        "    part: 74HC04",
        "    pins:",
        f"      A: net_cp_y{idx}",
        f"      Y: {inv_y}",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
        f"  - ref: U_CP_EN_{idx}",
        "    part: 74HC08",
        "    pins:",
        f"      A: {inv_y}",
        "      B: net_cmp_n",
        f"      Y: {and1}",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    if halt_mask:
        lines += [
            f"  - ref: U_CP_PRE_{idx}",
            "    part: 74HC08",
            "    pins:",
            "      A: net_clk2",
            f"      B: {and1}",
            f"      Y: {pre}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
            f"  - ref: U_CP_CLK_{idx}",
            "    part: 74HC08",
            "    pins:",
            f"      A: {pre}",
            "      B: net_halt_n",
            f"      Y: net_cp_r{idx}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
    else:
        lines += [
            f"  - ref: U_CP_CLK_{idx}",
            "    part: 74HC08",
            "    pins:",
            "      A: net_clk2",
            f"      B: {and1}",
            f"      Y: net_cp_r{idx}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
    return lines


def imm_dst_override() -> list[str]:
    return [
        "  - ref: U_IMM_BUS",
        "    part: 74HC08",
        "    pins:",
        "      A: net_bus_en0",
        "      B: net_bus_en1",
        "      Y: net_bus_imm",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
        "  - ref: U_DST0_MUX",
        "    part: 74HC157",
        "    pins:",
        "      1A: net_dst_reg0",
        "      1B: pwr_gnd",
        "      1Y: net_dst_eff0",
        "      S: net_bus_imm",
        "      OE: pwr_gnd",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
        "  - ref: U_DST1_MUX",
        "    part: 74HC157",
        "    pins:",
        "      1A: net_dst_reg1",
        "      1B: pwr_vcc",
        "      1Y: net_dst_eff1",
        "      S: net_bus_imm",
        "      OE: pwr_gnd",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--halt-mask",
        action="store_true",
        help="AND reg CP with ~HALT (Phase3 cpu_datapath_p3)",
    )
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=OUT_DEFAULT,
        help="Output yaml path (default: hw/netlist/blocks/regfile.yaml)",
    )
    args = ap.parse_args()
    halt_mask = args.halt_mask
    out_path: Path = args.out
    block_name = "regfile_halt" if halt_mask and out_path.name != "regfile.yaml" else "regfile"

    inst: list[str] = []
    for i in range(4):
        inst.extend(reg574(f"U_REG_R{i}", i))
    for p in range(4):
        inst.extend(mux153_pair(f"U_MUX_A_{p}", "a", p * 2))
        inst.extend(mux153_pair(f"U_MUX_B_{p}", "b", p * 2))
    for bit in range(8):
        inst.extend(imm_b_mux(bit))
    inst.extend(imm_dst_override())
    inst += [
        "  - ref: U_CP_DEC",
        "    part: 74HC138",
        "    pins:",
        "      A0: net_dst_eff0",
        "      A1: net_dst_eff1",
        "      A2: pwr_gnd",
        "      E1: pwr_gnd",
        "      E2: pwr_gnd",
        "      E3: pwr_vcc",
        "      Y0: net_cp_y0",
        "      Y1: net_cp_y1",
        "      Y2: net_cp_y2",
        "      Y3: net_cp_y3",
        "      Y4: net_cp_y4",
        "      Y5: net_cp_y5",
        "      Y6: net_cp_y6",
        "      Y7: net_cp_y7",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    for i in range(4):
        inst.extend(cp_gate(i, halt_mask=halt_mask))
    if halt_mask:
        inst += [
            "  - ref: U_HALT_N",
            "    part: 74HC04",
            "    pins:",
            "      A: net_halt",
            "      Y: net_halt_n",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]

    nets = [
        "  - name: net_clk2",
        "    width: 1",
        "    probes: [clk]",
        "  - name: net_src_reg0",
        "    width: 1",
        "  - name: net_src_reg1",
        "    width: 1",
        "  - name: net_dst_reg0",
        "    width: 1",
        "  - name: net_dst_reg1",
        "    width: 1",
        "  - name: net_bus_en0",
        "    width: 1",
        "  - name: net_bus_en1",
        "    width: 1",
        "  - name: net_cmp_n",
        "    width: 1",
    ]
    if halt_mask:
        nets += [
            "  - name: net_halt",
            "    width: 1",
            "  - name: net_halt_n",
            "    width: 1",
        ]
    nets += [
        "  - name: net_bus_imm",
        "    width: 1",
        "  - name: net_dst_eff0",
        "    width: 1",
        "  - name: net_dst_eff1",
        "    width: 1",
    ]
    for i in range(6):
        nets += [f"  - name: net_ctrl{i}", "    width: 1"]
    for i in range(8):
        nets += [f"  - name: net_cp_y{i}", "    width: 1"]
    for i in range(4):
        nets += [f"  - name: net_cp_r{i}", "    width: 1"]
        for b in range(8):
            line = f"  - name: net_r{i}_q{b}"
            if i == 2 and b == 0:
                line += "\n    width: 1\n    probes: [r2_q0]"
            elif i == 2 and b == 7:
                line += "\n    width: 1\n    probes: [r2_q7]"
            else:
                line += "\n    width: 1"
            nets.append(line)
    for b in range(8):
        nets += [f"  - name: net_a{b}", "    width: 1", f"  - name: net_b{b}", "    width: 1"]
        nets += [f"  - name: net_b153_{b}", "    width: 1"]
        if b == 0:
            nets += [f"  - name: net_y{b}", "    width: 1", "    probes: [y0]"]
        else:
            nets += [f"  - name: net_y{b}", "    width: 1"]
    nets += ["  - name: pwr_vcc", "    width: 1", "  - name: pwr_gnd", "    width: 1"]
    for i in range(4):
        nets += [f"  - name: net_cp_inv_r{i}", "    width: 1"]
        nets += [f"  - name: net_cp_en_r{i}", "    width: 1"]

    text = (
        f"version: 1\nblock: {block_name}\ninstances:\n"
        + "\n".join(inst)
        + "\nnets:\n"
        + "\n".join(nets)
        + "\n"
    )
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
