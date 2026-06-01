"""Load and print DIP pinout tables from hw/pinout/."""

from __future__ import annotations

from pathlib import Path

from hwsim import yaml_util


def pinout_root() -> Path:
    return Path(__file__).resolve().parents[1] / "hw" / "pinout"


def normalize_part(name: str) -> str:
    return name.strip().upper().replace("SN", "").replace("CD", "")


def list_parts() -> list[str]:
    idx = pinout_root() / "index.yaml"
    if not idx.is_file():
        return []
    data = yaml_util.load_file(str(idx))
    if not isinstance(data, dict):
        return []
    out: list[str] = []
    for entry in data.get("packages", []):
        if isinstance(entry, dict) and "part" in entry:
            out.append(str(entry["part"]))
    return out


def resolve_pinout_path(part: str) -> Path | None:
    key = normalize_part(part)
    idx = pinout_root() / "index.yaml"
    if idx.is_file():
        data = yaml_util.load_file(str(idx))
        if isinstance(data, dict):
            for entry in data.get("packages", []):
                if not isinstance(entry, dict):
                    continue
                if normalize_part(str(entry.get("part", ""))) == key:
                    rel = entry.get("file")
                    if rel:
                        p = pinout_root() / str(rel)
                        if p.is_file():
                            return p
    dip = pinout_root() / "dip"
    if dip.is_dir():
        for path in sorted(dip.glob("*.yaml")):
            data = yaml_util.load_file(str(path))
            if isinstance(data, dict) and normalize_part(str(data.get("part", ""))) == key:
                return path
    return None


def load_pinout(part: str) -> dict:
    path = resolve_pinout_path(part)
    if not path:
        raise FileNotFoundError(f"No DIP pinout for {part!r} under hw/pinout/")
    data = yaml_util.load_file(str(path))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid pinout file: {path}")
    data["_path"] = str(path)
    return data


def format_pinout_table(data: dict) -> str:
    part = data.get("part", "?")
    pkg = data.get("package", {})
    pkg_name = pkg.get("name", "?") if isinstance(pkg, dict) else "?"
    lines = [f"{part} - {pkg_name} ({data.get('_path', '')})", ""]
    lines.append("| Pin | Symbol | Role | Description |")
    lines.append("|-----|--------|------|-------------|")
    pins = data.get("pins", {})
    if isinstance(pins, dict):
        def _pin_num(s: str) -> int:
            return int(str(s).strip("\"'"))

        for num in sorted(pins.keys(), key=_pin_num):
            ent = pins[num]
            if not isinstance(ent, dict):
                continue
            sym = ent.get("sym", "")
            aliases = ent.get("aliases", [])
            if isinstance(aliases, list) and aliases:
                sym = f"{sym} ({', '.join(str(a) for a in aliases)})"
            pin_label = str(num).strip("\"'")
            role = ent.get("role", "")
            desc = ent.get("desc", "")
            lines.append(f"| {pin_label} | {sym} | {role} | {desc} |")
    gates = data.get("gates")
    if isinstance(gates, dict):
        lines.extend(["", "**Gates (logical → DIP pin):**", ""])
        for gid, g in sorted(gates.items()):
            if isinstance(g, dict):
                lines.append(f"- Gate {gid}: {g}")
    plover = data.get("plover_netlist")
    if isinstance(plover, dict):
        lines.extend(["", "**Plover netlist notes:**", ""])
        if plover.get("note"):
            lines.append(str(plover["note"]))
        m = plover.get("map")
        if isinstance(m, dict):
            lines.append("")
            lines.append("| Netlist | DIP | Datasheet |")
            lines.append("|---------|-----|-----------|")
            for k, v in sorted(m.items()):
                if isinstance(v, dict):
                    lines.append(f"| {k} | {v.get('dip', '')} | {v.get('datasheet', '')} |")
    sources = data.get("sources", [])
    if sources:
        lines.extend(["", "**Sources:**", ""])
        for s in sources:
            if isinstance(s, dict):
                url = s.get("url", "")
                doc = s.get("doc", s.get("org", ""))
                lines.append(f"- [{doc}]({url})" if url else f"- {doc}")
    return "\n".join(lines)
