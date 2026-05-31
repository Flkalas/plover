"""Compare KiCad S-expression netlist to YAML netlist."""

from __future__ import annotations

import re
from pathlib import Path

from hwsim.netlist import load_netlist


def _parse_kicad_netlist(path: Path) -> dict[tuple[str, str], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    connections: dict[tuple[str, str], str] = {}
    skip_names = {"VCC", "GND", "+5V", "UNCONNECTED-PAD"}

    for net_m in re.finditer(
        r"\(net\s+\(code\s+\"[^\"]*\"\)\s+\(name\s+\"([^\"]+)\"\)",
        text,
    ):
        net_name = net_m.group(1)
        if net_name.upper() in skip_names or "unconnected" in net_name.lower():
            continue
        rest = text[net_m.end() :]
        nxt = rest.find("(net ")
        segment = rest[:nxt] if nxt != -1 else rest[:2000]
        for node_m in re.finditer(
            r"\(node\s+\(ref\s+\"([^\"]+)\"\)\s+\(pin\s+\"[^\"]*\"\)"
            r"(?:\s+\(pinfunction\s+\"([^\"]+)\"\))?",
            segment,
        ):
            ref = node_m.group(1)
            pinfunc = node_m.group(2)
            if not pinfunc:
                pin_m = re.search(r'\(pin\s+"([^"]+)"\)', node_m.group(0))
                pinfunc = pin_m.group(1) if pin_m else "?"
            connections[(ref, pinfunc)] = net_name
    return connections


def _yaml_connections(path: Path) -> dict[tuple[str, str], str]:
    nl = load_netlist(path)
    out: dict[tuple[str, str], str] = {}
    for inst in nl.instances:
        for pin, net in inst.pins.items():
            if pin in ("VCC", "VDD", "GND", "VSS") or net.startswith("pwr_"):
                continue
            out[(inst.ref, pin)] = net
    return out


def diff_kicad(kicad_path: Path, yaml_path: Path) -> list[str]:
    if not kicad_path.is_file():
        return [f"KiCad netlist not found: {kicad_path}"]
    kicad = _parse_kicad_netlist(kicad_path)
    yaml_c = _yaml_connections(yaml_path)
    mismatches: list[str] = []
    for key, ynet in sorted(yaml_c.items()):
        if key not in kicad:
            mismatches.append(f"missing in KiCad: {key[0]}.{key[1]} -> {ynet}")
            continue
        knet = kicad[key]
        if _normalize_net(knet) != _normalize_net(ynet):
            mismatches.append(f"{key[0]}.{key[1]}: KiCad={knet} YAML={ynet}")
    return mismatches


def _normalize_net(name: str) -> str:
    return name.replace("/", "_").replace("-", "_").lower()
