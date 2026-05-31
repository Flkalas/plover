"""Generate hw/netlist/blocks/alu_b3.yaml (alu8 + 574 ACC)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALU8 = ROOT / "hw" / "netlist" / "blocks" / "alu8.yaml"


def main() -> None:
    text = ALU8.read_text(encoding="utf-8")
    text = text.replace("block: alu8", "block: alu_b3", 1)

    inst574 = [
        "  - ref: U_REG_574_ACC",
        "    part: 74HC574",
        "    pins:",
    ]
    for i in range(8):
        inst574.append(f"      D{i}: net_y{i}")
        inst574.append(f"      Q{i}: net_q{i}")
    inst574 += [
        "      CP: net_clk",
        "      OE: pwr_gnd",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]

    marker = "nets:"
    head, tail = text.split(marker, 1)
    head = head.rstrip() + "\n" + "\n".join(inst574) + "\n"
    extra_nets = [
        "  - name: net_clk",
        "    width: 1",
        "    probes: [clk]",
    ]
    for i in range(8):
        extra_nets += [f"  - name: net_q{i}", "    width: 1"]
        if i in (0, 7):
            extra_nets.append(f"    probes: [q{i}]")

    out = head + marker + "\n" + "\n".join(extra_nets) + "\n" + tail
    dest = ROOT / "hw" / "netlist" / "blocks" / "alu_b3.yaml"
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
