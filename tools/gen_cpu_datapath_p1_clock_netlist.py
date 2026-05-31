"""Merge clock + alu_decode + regfile + alu8 -> cpu_datapath_p1_clock.yaml."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = [
    ROOT / "hw" / "netlist" / "blocks" / "clock.yaml",
    ROOT / "hw" / "netlist" / "blocks" / "alu_decode.yaml",
    ROOT / "hw" / "netlist" / "blocks" / "regfile.yaml",
    ROOT / "hw" / "netlist" / "blocks" / "alu8.yaml",
]
OUT = ROOT / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_clock.yaml"


def _split(text: str) -> tuple[str, str]:
    _, rest = text.split("instances:", 1)
    inst, nets = rest.split("nets:", 1)
    return inst, nets


def main() -> None:
    inst_parts: list[str] = []
    net_parts: list[str] = []
    for path in BLOCKS:
        inst, nets = _split(path.read_text(encoding="utf-8"))
        inst_parts.append(inst)
        net_parts.append(nets)
    out = (
        "version: 1\nblock: cpu_datapath_p1_clock\ninstances:"
        + "".join(inst_parts)
        + "nets:"
        + "".join(net_parts)
    )
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
