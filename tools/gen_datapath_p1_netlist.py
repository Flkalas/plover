"""Merge alu8_decode + regfile_574 + Y_BUS_BUF -> datapath_p1.yaml."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEC_ALU = ROOT / "hw" / "netlist" / "blocks" / "alu8_decode.yaml"
REG = ROOT / "hw" / "netlist" / "blocks" / "regfile_574.yaml"
OUT = ROOT / "hw" / "netlist" / "blocks" / "datapath_p1.yaml"

_NET_RE = re.compile(
    r"  - name: (net_\w+)\n(?:    width: \d+\n)?(?:    probes: \[[^\]]*\]\n)?",
    re.MULTILINE,
)


def _split_yaml(text: str) -> tuple[str, str, str]:
    head, rest = text.split("instances:", 1)
    inst, nets_tail = rest.split("nets:", 1)
    return head, inst, nets_tail


def _rewire_regfile(inst: str) -> str:
    for i in range(8):
        inst = inst.replace(f"QA{i}: net_qa{i}", f"QA{i}: net_a{i}")
        inst = inst.replace(f"QB{i}: net_qb{i}", f"QB{i}: net_b{i}")
    return inst


def _collect_nets(nets_tail: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _NET_RE.finditer(nets_tail):
        name = m.group(1)
        out[name] = m.group(0)
    return out


def _y_bus_buf_block() -> str:
    lines = [
        "  - ref: U_Y_BUS_BUF",
        "    part: Y_BUS_BUF",
        "    pins:",
        "      Y_OE: net_y_oe",
    ]
    for i in range(8):
        lines.append(f"      Y{i}: net_y{i}")
        lines.append(f"      D{i}: net_d{i}")
    return "\n".join(lines) + "\n"


def main() -> None:
    dec = DEC_ALU.read_text(encoding="utf-8")
    reg = REG.read_text(encoding="utf-8")
    _, dec_inst, dec_nets = _split_yaml(dec)
    _, reg_inst, reg_nets = _split_yaml(reg)
    reg_inst = _rewire_regfile(reg_inst)

    nets: dict[str, str] = {}
    nets.update(_collect_nets(dec_nets))
    for name, block in _collect_nets(reg_nets).items():
        if name.startswith("net_qa") or name.startswith("net_qb"):
            continue
        if name not in nets:
            nets[name] = block
    nets.setdefault("net_y_oe", "  - name: net_y_oe\n    width: 1\n    probes: [y_oe]\n")

    out = (
        "version: 1\nblock: datapath_p1\n"
        "description: v0.1 Execute slice — alu8_decode + 574 GPR + Y bus buffer\n"
        "instances:"
        + dec_inst
        + reg_inst
        + _y_bus_buf_block()
        + "nets:\n"
        + "".join(nets[name] for name in sorted(nets.keys()))
    )
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
