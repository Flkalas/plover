"""Merge alu_decode.yaml + alu8.yaml -> alu8_decode.yaml."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEC = ROOT / "hw" / "netlist" / "blocks" / "alu_decode.yaml"
ALU8 = ROOT / "hw" / "netlist" / "blocks" / "alu8.yaml"
OUT = ROOT / "hw" / "netlist" / "blocks" / "alu8_decode.yaml"


def _split_yaml(text: str) -> tuple[str, str, str]:
    head, rest = text.split("instances:", 1)
    inst, nets_tail = rest.split("nets:", 1)
    return head, inst, nets_tail


def main() -> None:
    dec = DEC.read_text(encoding="utf-8")
    alu = ALU8.read_text(encoding="utf-8")

    dec_head, dec_inst, dec_nets = _split_yaml(dec)
    alu_head, alu_inst, alu_nets = _split_yaml(alu)

    out = (
        "version: 1\nblock: alu8_decode\ninstances:"
        + dec_inst
        + alu_inst
        + "nets:"
        + dec_nets
        + alu_nets
    )
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
