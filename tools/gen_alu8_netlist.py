"""Generate hw/netlist/blocks/alu8.yaml with 157 B cascade."""
from __future__ import annotations

from pathlib import Path


def main() -> None:
    lines = ["version: 1", "block: alu8", "instances:"]

    for tag, a_lo, cin, cout in [("LO", 0, "net_cin", "net_c_lo"), ("HI", 4, "net_c_lo", "net_c_hi")]:
        lines += [f"  - ref: U_ALU_283_{tag}", "    part: 74HC283", "    pins:"]
        for i in range(4):
            lines.append(f"      A{i}: net_a{a_lo + i}")
            lines.append(f"      B{i}: net_b_add{a_lo + i}")
        lines.append(f"      C0: {cin}")
        for i in range(4):
            lines.append(f"      S{i}: net_sum{a_lo + i}")
        lines.append(f"      C4: {cout}")
        lines += ["      VCC: pwr_vcc", "      GND: pwr_gnd"]

    for i in range(8):
        lines += [
            f"  - ref: U_ALU_86_INV_{i}",
            "    part: 74HC86",
            "    pins:",
            f"      A: net_b{i}",
            "      B: net_sub_en",
            f"      Y: net_b_inv{i}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
        lines += [
            f"  - ref: U_ALU_86_XOR_{i}",
            "    part: 74HC86",
            "    pins:",
            f"      A: net_a{i}",
            f"      B: net_b{i}",
            f"      Y: net_xor{i}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
        lines += [
            f"  - ref: U_ALU_08_{i}",
            "    part: 74HC08",
            "    pins:",
            f"      A: net_a{i}",
            f"      B: net_b{i}",
            f"      Y: net_and{i}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
        lines += [
            f"  - ref: U_ALU_32_{i}",
            "    part: 74HC32",
            "    pins:",
            f"      A: net_a{i}",
            f"      B: net_b{i}",
            f"      Y: net_or{i}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]
        lines += [
            f"  - ref: U_ALU_04_N{i}",
            "    part: 74HC04",
            "    pins:",
            f"      A: net_a{i}",
            f"      Y: net_not{i}",
            "      VCC: pwr_vcc",
            "      GND: pwr_gnd",
        ]

    for chip in range(2):
        lines += [f"  - ref: U_ALU_157_B_{chip}", "    part: 74HC157", "    pins:"]
        for ch in range(1, 5):
            bit = chip * 4 + ch - 1
            lines += [f"      {ch}A: net_b{bit}", f"      {ch}B: net_b_inv{bit}", f"      {ch}Y: net_b_path{bit}"]
        lines += ["      S: net_b_sel", "      OE: pwr_gnd", "      VCC: pwr_vcc", "      GND: pwr_gnd"]

    for chip in range(2):
        lines += [f"  - ref: U_ALU_157_B2_{chip}", "    part: 74HC157", "    pins:"]
        for ch in range(1, 5):
            bit = chip * 4 + ch - 1
            bpin = "pwr_vcc" if bit == 0 else f"net_b_const_bit{bit}"
            lines += [f"      {ch}A: net_b_path{bit}", f"      {ch}B: {bpin}", f"      {ch}Y: net_b_add{bit}"]
        lines += ["      S: net_b_const_sel", "      OE: pwr_gnd", "      VCC: pwr_vcc", "      GND: pwr_gnd"]

    for chip in range(2):
        lines += [f"  - ref: U_ALU_157_OUT_{chip}", "    part: 74HC157", "    pins:"]
        for ch in range(1, 5):
            bit = chip * 4 + ch - 1
            lines += [f"      {ch}A: net_xor{bit}", f"      {ch}B: net_not{bit}", f"      {ch}Y: net_c3_{bit}"]
        lines += ["      S: net_c3_sel", "      OE: pwr_gnd", "      VCC: pwr_vcc", "      GND: pwr_gnd"]

    for chip in range(4):
        lines += [f"  - ref: U_ALU_153_{chip}", "    part: 74HC153", "    pins:"]
        b0, b1 = chip * 2, chip * 2 + 1
        for ch, bit in [("1", b0), ("2", b1)]:
            lines += [
                f"      {ch}C0: net_sum{bit}",
                f"      {ch}C1: net_and{bit}",
                f"      {ch}C2: net_or{bit}",
                f"      {ch}C3: net_c3_{bit}",
                f"      {ch}G: pwr_gnd",
                f"      {ch}Y: net_y{bit}",
            ]
        lines += ["      A: net_153_s0", "      B: net_153_s1", "      VCC: pwr_vcc", "      GND: pwr_gnd"]

    lines.append("nets:")
    for i in range(8):
        lines += [f"  - name: net_a{i}", "    width: 1", f"  - name: net_b{i}", "    width: 1"]
    for name in (
        "net_sub_en",
        "net_cin",
        "net_153_s0",
        "net_153_s1",
        "net_b_sel",
        "net_b_const_sel",
        "net_c3_sel",
    ):
        lines += [f"  - name: {name}", "    width: 1"]
    for i in range(1, 8):
        lines += [f"  - name: net_b_const_bit{i}", "    width: 1"]
    for i in range(8):
        for prefix in (
            "net_b_inv",
            "net_b_path",
            "net_b_add",
            "net_sum",
            "net_and",
            "net_or",
            "net_xor",
            "net_not",
            "net_c3_",
        ):
            lines += [f"  - name: {prefix}{i}", "    width: 1"]
    for i in range(8):
        lines += [f"  - name: net_y{i}", "    width: 1"]
        if i in (0, 7):
            lines.append(f"    probes: [y{i}]")
    lines += [
        "  - name: net_c_lo",
        "    width: 1",
        "  - name: net_c_hi",
        "    width: 1",
        "    probes: [carry_hi]",
        "  - name: pwr_vcc",
        "    width: 1",
        "  - name: pwr_gnd",
        "    width: 1",
    ]

    out = Path(__file__).resolve().parents[1] / "hw" / "netlist" / "blocks" / "alu8.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
