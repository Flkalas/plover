"""ALU8 schematic layout document (YAML metadata for export; not a web viewer)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from simulators.cyclesim.export.alu8_netlist import BLOCK_NAME, DESCRIPTION, dump_yaml


def build_alu8_schematic_doc() -> dict[str, Any]:
    return {
        "version": 1,
        "block": BLOCK_NAME,
        "description": f"Schematic layout for {DESCRIPTION}",
        "source": {"netlist": BLOCK_NAME},
        "template": "alu8_row_grid",
        "rows": 8,
        "port_groups": {
            "a": {
                "nets": [f"net_a{i}" for i in range(8)],
                "edge": "left",
                "align": "row",
            },
            "b": {
                "nets": [f"net_b{i}" for i in range(8)],
                "edge": "left",
                "align": "row",
            },
            "lgc": {
                "nets": [f"net_lgc{i}" for i in range(4)],
                "edge": "left",
                "corridor": "above_153",
            },
            "bctrl": {
                "nets": [f"net_bctrl{i}" for i in range(4)],
                "edge": "left",
                "corridor": "below_153",
            },
            "ctrl": {
                "nets": ["net_cin", "net_153_s0", "net_153_s1"],
                "edge": "left",
            },
            "y_mux": {
                "nets": ["net_y_mux_sel"],
                "edge": "left",
                "corridor": "below_stack",
            },
            "y": {
                "nets": [f"net_y{i}" for i in range(8)],
                "edge": "right",
                "align": "row",
            },
            "flags": {
                "nets": ["net_cmp_z", "net_cmp_c_ge", "net_c_hi"],
                "edge": "right",
            },
        },
        "orphan_ports": [
            "net_153_s0",
            "net_153_s1",
            "net_cmp_z",
            "net_cmp_c_ge",
        ],
    }


def write_alu8_schematic_doc(path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(build_alu8_schematic_doc()), encoding="utf-8")
    return path
