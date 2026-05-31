"""Generate hw/netlist/blocks/flg_latch.yaml — Z/C flag latch (behavioral FLG_LATCH)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "netlist" / "blocks" / "flg_latch.yaml"


def build() -> str:
    pins = [
        "      CP: net_clk2",
        "      WE: net_flg_we",
        "      C_IN: net_c_hi",
    ]
    for i in range(8):
        pins.append(f"      Y{i}: net_y{i}")
    pins += [
        "      Z: net_z_flg",
        "      C: net_c_flg",
        "      Z_PREV: net_z_prev",
        "      VCC: pwr_vcc",
        "      GND: pwr_gnd",
    ]
    inst = [
        "  - ref: U_FLG",
        "    part: FLG_LATCH",
        "    pins:",
        *pins,
    ]
    nets = [
        "  - name: net_clk2",
        "    width: 1",
        "    probes: [clk]",
        "  - name: net_flg_we",
        "    width: 1",
        "  - name: net_c_hi",
        "    width: 1",
        "  - name: net_z_flg",
        "    width: 1",
        "  - name: net_c_flg",
        "    width: 1",
        "  - name: net_z_prev",
        "    width: 1",
    ]
    for i in range(8):
        nets += [f"  - name: net_y{i}", "    width: 1"]
    nets += ["  - name: pwr_vcc", "    width: 1", "  - name: pwr_gnd", "    width: 1"]
    return (
        "version: 1\nblock: flg_latch\ninstances:\n"
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
