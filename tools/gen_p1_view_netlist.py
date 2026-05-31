"""Generate cpu_datapath_p1_view.yaml — probe-rich netlist for p1-viewer."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_clock.yaml"
OUT = ROOT / "hw" / "netlist" / "blocks" / "cpu_datapath_p1_view.yaml"

PROBE_MAP: dict[str, str] = {}
for i in range(4):
    PROBE_MAP[f"net_alu_op{i}"] = f"alu_op{i}"
for i in range(2):
    PROBE_MAP[f"net_src_reg{i}"] = f"src{i}"
    PROBE_MAP[f"net_dst_reg{i}"] = f"dst{i}"
    PROBE_MAP[f"net_bus_en{i}"] = f"bus{i}"
for i in range(8):
    PROBE_MAP[f"net_a{i}"] = f"a{i}"
    PROBE_MAP[f"net_b{i}"] = f"b{i}"
    PROBE_MAP[f"net_y{i}"] = f"y{i}"
for r in range(4):
    for i in range(8):
        PROBE_MAP[f"net_r{r}_q{i}"] = f"r{r}q{i}"
PROBE_MAP["net_cmp_n"] = "cmp_n"
PROBE_MAP["net_clk2"] = "clk2"
PROBE_MAP["net_sub_en"] = "sub_en"


def main() -> None:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    i = 0
    in_nets = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("block:"):
            out.append("block: cpu_datapath_p1_view")
            i += 1
            continue
        if line.strip() == "nets:":
            in_nets = True
            out.append(line)
            i += 1
            continue
        if in_nets and line.strip().startswith("- name:"):
            name = line.strip().split(":", 1)[1].strip()
            out.append(line)
            i += 1
            width_line = ""
            has_probe = False
            while i < len(lines) and lines[i].startswith("    "):
                if lines[i].strip().startswith("probes:"):
                    has_probe = True
                    label = PROBE_MAP.get(name)
                    if label:
                        out.append(f"    probes: [{label}]")
                    else:
                        out.append(lines[i])
                elif lines[i].strip().startswith("width:"):
                    width_line = lines[i]
                    out.append(lines[i])
                else:
                    out.append(lines[i])
                i += 1
            if name in PROBE_MAP and not has_probe:
                if width_line:
                    pass
                out.append(f"    probes: [{PROBE_MAP[name]}]")
            continue
        out.append(line)
        i += 1
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
