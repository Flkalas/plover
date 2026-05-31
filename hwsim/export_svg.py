"""Export block netlist as SVG wiring diagram."""

from __future__ import annotations

from hwsim.netlist import Netlist


def export_svg(nl: Netlist) -> str:
    w, h = 720, 80 + len(nl.instances) * 72
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<style>text{font-family:system-ui,sans-serif;font-size:12px;fill:#e6edf3}'
        ".chip{fill:#161b22;stroke:#30363d;stroke-width:1}"
        ".title{fill:#8b949e;font-size:11px}</style>",
        f'<rect width="{w}" height="{h}" fill="#0d1117"/>',
        f'<text x="16" y="24" class="title">block: {nl.block}</text>',
    ]
    y = 48
    for inst in nl.instances:
        lines.append(f'<rect class="chip" x="16" y="{y}" width="200" height="52" rx="4"/>')
        lines.append(f'<text x="28" y="{y + 20}">{inst.ref}</text>')
        lines.append(f'<text x="28" y="{y + 38}" class="title">{inst.part}</text>')
        pin_y = y + 8
        px = 240
        for pin, net in sorted(inst.pins.items()):
            if pin in ("VCC", "VDD", "GND", "VSS") or net.startswith("pwr_"):
                continue
            lines.append(f'<text x="{px}" y="{pin_y + 14}">{pin} → {net}</text>')
            pin_y += 16
            if pin_y > y + 48:
                px += 180
                pin_y = y + 8
        y += 72
    lines.append("</svg>")
    return "\n".join(lines)
