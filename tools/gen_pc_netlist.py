"""Generate hw/netlist/blocks/pc.yaml — 4x 74HC161 16-bit PC with branch load."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "netlist" / "blocks" / "pc.yaml"


def hc161(
    ref: str,
    q_base: int,
    p_regs: list[tuple[int, int]],
    *,
    cep: str,
    cet: str,
    tc: str | None = None,
) -> list[str]:
    lines = [f"  - ref: {ref}", "    part: 74HC161", "    pins:"]
    for i in range(4):
        r, b = p_regs[i]
        lines.append(f"      P{i}: net_r{r}_q{b}")
    for i in range(4):
        lines.append(f"      Q{i}: net_pc{q_base + i}")
    lines += [
        f"      CEP: {cep}",
        f"      CET: {cet}",
        "      CP: net_clk2",
        "      MR: pwr_vcc",
        "      PE: net_pc_load",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    if tc:
        lines.insert(-4, f"      TC: {tc}")
    return lines


def build() -> str:
    inst: list[str] = []
    inst.extend(
        hc161(
            "U_PC_0",
            0,
            [(0, i) for i in range(4)],
            cep="net_pc_count_en",
            cet="pwr_vcc",
            tc="net_pc_tc0",
        )
    )
    inst.extend(
        hc161(
            "U_PC_1",
            4,
            [(0, i) for i in range(4, 8)],
            cep="net_pc_tc0",
            cet="net_pc_count_en",
            tc="net_pc_tc1",
        )
    )
    inst.extend(
        hc161(
            "U_PC_2",
            8,
            [(1, i) for i in range(4)],
            cep="net_pc_tc1",
            cet="net_pc_count_en",
            tc="net_pc_tc2",
        )
    )
    inst.extend(
        hc161(
            "U_PC_3",
            12,
            [(1, i) for i in range(4, 8)],
            cep="net_pc_tc2",
            cet="net_pc_count_en",
        )
    )

    nets = [
        "  - name: net_clk2",
        "    width: 1",
        "    probes: [clk]",
        "  - name: net_pc_load",
        "    width: 1",
        "  - name: net_pc_count_en",
        "    width: 1",
        "  - name: net_pc_tc0",
        "    width: 1",
        "  - name: net_pc_tc1",
        "    width: 1",
        "  - name: net_pc_tc2",
        "    width: 1",
    ]
    for i in range(16):
        probe = "\n    probes: [pc]" if i == 0 else ""
        nets.append(f"  - name: net_pc{i}\n    width: 1{probe}")
    for r in range(2):
        for b in range(8):
            nets += [f"  - name: net_r{r}_q{b}", "    width: 1"]
    nets += ["  - name: pwr_vcc", "    width: 1", "  - name: pwr_gnd", "    width: 1"]

    return (
        "version: 1\nblock: pc\ninstances:\n"
        + "\n".join(inst)
        + "\nnets:\n"
        + "\n".join(nets)
        + "\n"
    )


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
