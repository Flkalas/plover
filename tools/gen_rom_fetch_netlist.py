"""Generate hw/netlist/blocks/rom_fetch.yaml (+ optional PC8 auto-increment)."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MANUAL = ROOT / "hw" / "netlist" / "blocks" / "rom_fetch.yaml"
OUT_PC8 = ROOT / "hw" / "netlist" / "blocks" / "rom_fetch_pc8.yaml"

# CW[15:0] = { alu_op[3:0], src[1:0], dst[1:0], bus_en[1:0], ctrl[5:0] }
CW_NETS = [
    (15, "net_alu_op3"),
    (14, "net_alu_op2"),
    (13, "net_alu_op1"),
    (12, "net_alu_op0"),
    (11, "net_src_reg1"),
    (10, "net_src_reg0"),
    (9, "net_dst_reg1"),
    (8, "net_dst_reg0"),
    (7, "net_bus_en1"),
    (6, "net_bus_en0"),
    (5, "net_ctrl5"),
    (4, "net_ctrl4"),
    (3, "net_ctrl3"),
    (2, "net_ctrl2"),
    (1, "net_ctrl1"),
    (0, "net_ctrl0"),
]


def rom_instance() -> list[str]:
    lines = [
        "  - ref: U_ROM",
        "    part: ROM16",
        "    pins:",
    ]
    for i in range(8):
        lines.append(f"      A{i}: net_pc{i}")
    for bit, net in CW_NETS:
        lines.append(f"      D{bit}: {net}")
    lines += [
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    return lines


def pc8_instance() -> list[str]:
    lines = [
        "  - ref: U_PC8",
        "    part: PC8_AUTO",
        "    pins:",
        "      CP: net_clk2",
    ]
    for i in range(8):
        lines.append(f"      Q{i}: net_pc{i}")
    lines += [
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    return lines


def net_defs(include_pc8: bool) -> list[str]:
    nets = [
        "  - name: net_clk2",
        "    width: 1",
        "    probes: [clk]",
    ]
    for i in range(8):
        probe = "    probes: [pc]" if i == 0 and include_pc8 else ""
        line = f"  - name: net_pc{i}\n    width: 1"
        if probe:
            line += f"\n{probe}"
        nets.append(line)
    for _bit, net in CW_NETS:
        if net.startswith("net_alu_op"):
            nets.append(f"  - name: {net}\n    width: 1")
        elif net.startswith("net_ctrl"):
            nets.append(f"  - name: {net}\n    width: 1")
        else:
            nets.append(f"  - name: {net}\n    width: 1")
    nets += ["  - name: pwr_vcc", "    width: 1", "  - name: pwr_gnd", "    width: 1"]
    return nets


def build(include_pc8: bool) -> str:
    block = "rom_fetch_pc8" if include_pc8 else "rom_fetch"
    inst: list[str] = []
    if include_pc8:
        inst.extend(pc8_instance())
    inst.extend(rom_instance())
    return (
        f"version: 1\nblock: {block}\ninstances:\n"
        + "\n".join(inst)
        + "\nnets:\n"
        + "\n".join(net_defs(include_pc8))
        + "\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pc8", action="store_true", help="Include PC8 auto-increment stub")
    args = ap.parse_args()
    if args.pc8:
        OUT_PC8.write_text(build(True), encoding="utf-8")
        print(f"wrote {OUT_PC8}")
    else:
        OUT_MANUAL.write_text(build(False), encoding="utf-8")
        print(f"wrote {OUT_MANUAL}")


if __name__ == "__main__":
    main()
