"""Generate hw/netlist/blocks/alu8.yaml — pure Gigatron B_CTRL bit-slice (153×8, 12 DIP)."""
from __future__ import annotations

from pathlib import Path


def _emit_283(lines: list[str], tag: str, a_lo: int, cin: str, cout: str) -> None:
    lines += [f"  - ref: U_ALU_283_{tag}", "    part: 74HC283", "    pins:"]
    for i in range(4):
        lines.append(f"      A{i}: net_a{a_lo + i}")
        lines.append(f"      B{i}: net_b_add{a_lo + i}")
    lines.append(f"      C0: {cin}")
    for i in range(4):
        lines.append(f"      S{i}: net_sum{a_lo + i}")
    lines.append(f"      C4: {cout}")
    lines += ["      VCC: pwr_vcc", "      GND: pwr_gnd"]


def _emit_153_bit(lines: list[str], bit: int) -> None:
    """Gigatron bit-slice: mux1=lgc on 1C*, mux2=bctrl on 2C*; A/B = operand select."""
    lines += [
        f"  - ref: U_ALU_153_{bit}",
        "    part: 74HC153",
        "    pins:",
        "      1C0: net_lgc0",
        "      1C1: net_lgc1",
        "      1C2: net_lgc2",
        "      1C3: net_lgc3",
        "      1G: pwr_gnd",
        f"      1Y: net_y_logic{bit}",
        "      2C0: net_bctrl0",
        "      2C1: net_bctrl1",
        "      2C2: net_bctrl2",
        "      2C3: net_bctrl3",
        "      2G: pwr_gnd",
        f"      2Y: net_b_add{bit}",
        f"      A: net_a{bit}",
        f"      B: net_b{bit}",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]


def _emit_157_ybp(lines: list[str], chip: int) -> None:
    lines += [f"  - ref: U_ALU_157_YBP_{chip}", "    part: 74HC157", "    pins:"]
    for ch in range(1, 5):
        bit = chip * 4 + ch - 1
        lines += [
            f"      {ch}A: net_sum{bit}",
            f"      {ch}B: net_y_logic{bit}",
            f"      {ch}Y: net_y{bit}",
        ]
    lines += ["      S: net_y_mux_sel", "      OE: pwr_gnd", "      VCC: pwr_vcc", "      GND: pwr_gnd"]


def _emit_cmp_sub(lines: list[str]) -> None:
    lines += ["  - ref: U_ALU_CMP_SUB", "    part: ALU_CMP_SUB", "    pins:"]
    for i in range(8):
        lines.append(f"      Y{i}: net_y{i}")
    lines += [
        "      C_HI: net_c_hi",
        "      CIN: net_cin",
        "      BCTRL0: net_bctrl0",
        "      BCTRL1: net_bctrl1",
        "      BCTRL2: net_bctrl2",
        "      BCTRL3: net_bctrl3",
        "      Z: net_cmp_z",
        "      C_GE: net_cmp_c_ge",
    ]


def main() -> None:
    lines = ["version: 1", "block: alu8", "instances:"]

    _emit_283(lines, "LO", 0, "net_cin", "net_c_lo")
    _emit_283(lines, "HI", 4, "net_c_lo", "net_c_hi")

    for bit in range(8):
        _emit_153_bit(lines, bit)

    for chip in range(2):
        _emit_157_ybp(lines, chip)

    lines += [
        "  - ref: U_ALU_Y_MUX_SEL",
        "    part: ALU_Y_MUX_SEL",
        "    pins:",
        "      S0: net_153_s0",
        "      S1: net_153_s1",
        "      SEL: net_y_mux_sel",
    ]

    _emit_cmp_sub(lines)

    lines.append("nets:")
    for i in range(8):
        lines += [f"  - name: net_a{i}", "    width: 1", f"  - name: net_b{i}", "    width: 1"]
    for name in (
        "net_cin",
        "net_153_s0",
        "net_153_s1",
        "net_bctrl0",
        "net_bctrl1",
        "net_bctrl2",
        "net_bctrl3",
        "net_lgc0",
        "net_lgc1",
        "net_lgc2",
        "net_lgc3",
        "net_y_mux_sel",
    ):
        lines += [f"  - name: {name}", "    width: 1"]
    lines += [
        "  - name: net_cmp_z",
        "    width: 1",
        "    probes: [cmp_z]",
        "  - name: net_cmp_c_ge",
        "    width: 1",
        "    probes: [cmp_c_ge]",
    ]

    for i in range(8):
        for prefix in ("net_b_add", "net_sum", "net_y_logic"):
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

    root = Path(__file__).resolve().parents[1]
    out = root / "hw" / "netlist" / "blocks" / "alu8.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    _patch_alu8_decode(root, out)


def _patch_alu8_decode(root: Path, alu8_path: Path) -> None:
    decode_path = root / "hw" / "netlist" / "blocks" / "alu8_decode.yaml"
    decode_only = root / "hw" / "netlist" / "blocks" / "alu_decode.yaml"
    if not decode_only.is_file():
        print(f"skip {decode_path.name}: run tools/gen_alu_decode_netlist.py first")
        return
    dec = decode_only.read_text(encoding="utf-8")
    alu = alu8_path.read_text(encoding="utf-8")
    dec_head, dec_inst, dec_nets = _split_yaml(dec)
    dec_nets = dec_nets.replace("  - name: net_sub_en\n    width: 1\n", "")
    _, alu_inst, alu_nets = _split_yaml(alu)
    alu_nets = _dedupe_alu_nets(dec_nets, alu_nets)
    merged = (
        "version: 1\nblock: alu8_decode\ninstances:"
        + dec_inst
        + alu_inst
        + "nets:"
        + dec_nets
        + alu_nets
    )
    decode_path.write_text(merged, encoding="utf-8")
    print(f"wrote {decode_path}")


def _split_yaml(text: str) -> tuple[str, str, str]:
    head, rest = text.split("instances:", 1)
    inst, nets_tail = rest.split("nets:", 1)
    return head, inst, nets_tail


def _dedupe_alu_nets(dec_nets: str, alu_nets: str) -> str:
    import re

    dec_names = set(re.findall(r"^- name: (net_\w+)", dec_nets, re.M))
    dec_names |= {"pwr_vcc", "pwr_gnd"}
    out: list[str] = []
    skip = False
    for line in alu_nets.splitlines():
        m = re.match(r"^- name: (\S+)", line)
        if m:
            skip = m.group(1) in dec_names
        if not skip:
            out.append(line)
    return "\n".join(out) + ("\n" if alu_nets.endswith("\n") else "")


if __name__ == "__main__":
    main()
