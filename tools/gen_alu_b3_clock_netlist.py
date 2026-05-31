"""Generate hw/netlist/blocks/alu_b3_clock.yaml (clock + alu_b3, CP on net_clk2)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOCK = ROOT / "hw" / "netlist" / "blocks" / "clock.yaml"
B3 = ROOT / "hw" / "netlist" / "blocks" / "alu_b3.yaml"
OUT = ROOT / "hw" / "netlist" / "blocks" / "alu_b3_clock.yaml"


def load_blocks(path: Path) -> tuple[str, list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    inst: list[str] = []
    nets: list[str] = []
    mode = None
    for line in lines:
        if line.startswith("block:"):
            continue
        if line.strip() == "instances:":
            mode = "inst"
            continue
        if line.strip() == "nets:":
            mode = "nets"
            continue
        if line.startswith("version:"):
            continue
        if mode == "inst":
            inst.append(line)
        elif mode == "nets":
            nets.append(line)
    return path.read_text(encoding="utf-8").split("block:")[0].strip(), inst, nets


def main() -> None:
    _ver, clock_inst, clock_nets = load_blocks(CLOCK)
    _b, b3_inst, b3_nets = load_blocks(B3)

    b3_inst_text = "\n".join(b3_inst)
    b3_inst_text = b3_inst_text.replace("CP: net_clk", "CP: net_clk2")

    skip_net = {"net_clk"}
    filtered_b3_nets: list[str] = []
    i = 0
    while i < len(b3_nets):
        line = b3_nets[i]
        if line.strip().startswith("- name: net_clk"):
            i += 1
            while i < len(b3_nets) and not b3_nets[i].strip().startswith("- name:"):
                i += 1
            continue
        filtered_b3_nets.append(line)
        i += 1

    clock_net_names = set()
    for line in clock_nets:
        s = line.strip()
        if s.startswith("- name:"):
            clock_net_names.add(s.split(":", 1)[1].strip())

    merged_nets = list(clock_nets)
    for line in filtered_b3_nets:
        s = line.strip()
        if s.startswith("- name:"):
            n = s.split(":", 1)[1].strip()
            if n in clock_net_names:
                continue
        merged_nets.append(line)

    out_lines = [
        "version: 1",
        "block: alu_b3_clock",
        "instances:",
        *clock_inst,
        *b3_inst_text.splitlines(),
        "nets:",
        *merged_nets,
        "",
    ]
    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
