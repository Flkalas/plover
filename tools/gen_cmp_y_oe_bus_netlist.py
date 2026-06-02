"""Generate hw/netlist/blocks/cmp_y_oe_bus.yaml — alu8 + Y_BUS_BUF (CW Y_OE → net_d)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hw" / "netlist" / "blocks" / "alu8.yaml"
OUT = ROOT / "hw" / "netlist" / "blocks" / "cmp_y_oe_bus.yaml"

Y_BUS_BUF = """
  - ref: U_Y_BUS_BUF
    part: Y_BUS_BUF
    pins:
      Y0: net_y0
      Y1: net_y1
      Y2: net_y2
      Y3: net_y3
      Y4: net_y4
      Y5: net_y5
      Y6: net_y6
      Y7: net_y7
      D0: net_d0
      D1: net_d1
      D2: net_d2
      D3: net_d3
      D4: net_d4
      D5: net_d5
      D6: net_d6
      D7: net_d7
      Y_OE: net_y_oe
"""

EXTRA_NETS = """
  - name: net_y_oe
    width: 1
    probes: [y_oe]
  - name: net_d0
    width: 1
    probes: [d0]
  - name: net_d1
    width: 1
  - name: net_d2
    width: 1
  - name: net_d3
    width: 1
  - name: net_d4
    width: 1
  - name: net_d5
    width: 1
  - name: net_d6
    width: 1
  - name: net_d7
    width: 1
    probes: [d7]
"""


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    text = text.replace("block: alu8", "block: cmp_y_oe_bus", 1)
    if "\nnets:\n" not in text:
        raise SystemExit(f"{SRC}: missing nets section")
    inst, nets = text.split("\nnets:\n", 1)
    out = inst.rstrip() + Y_BUS_BUF + "\nnets:\n" + nets.rstrip() + EXTRA_NETS + "\n"
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
