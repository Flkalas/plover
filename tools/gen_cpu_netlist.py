"""Generate hw/netlist/blocks/cpu.yaml — 574 GPR + system CPLD composite."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hw" / "netlist" / "blocks" / "cpu.yaml"

HEADER = """version: 1
block: cpu
description: "v0.1 CPU datapath — 574×4 GPR + ATF1504AS system CPLD (composite stub)"
includes:
  - regfile_574.yaml
  - cpld_system_ctrl.yaml
notes: |
  Full SoC netlist merges ALU8, addr_mux, sram256_dual, nor_flash.
  Generate with: python tools/gen_cpu_netlist.py
"""


def main() -> None:
    OUT.write_text(HEADER, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
