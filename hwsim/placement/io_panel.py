"""External I/O panel model (left / right variants)."""

from __future__ import annotations

from dataclasses import dataclass, field

from hwsim.export_schematic import (
    ASSEMBLY_IO_PANEL_PKG,
    PinAnchor,
    _IO_SECTIONS,
    _is_control_net,
    _net_color,
)
from hwsim.netlist import Netlist

# px inset from canvas edge when panel is on the right
IO_PANEL_EDGE_MARGIN = 4.0


@dataclass
class IoSectionSpec:
    name: str
    part: str
    nets: list[str]


@dataclass
class IoPanelSpec:
    side: str  # "left" | "right"
    sections: list[IoSectionSpec] = field(default_factory=list)
    canvas_width: float = 1200.0


def default_io_sections(nl: Netlist) -> list[IoSectionSpec]:
    defined = {n.name for n in nl.nets}
    sections: list[IoSectionSpec] = []
    part_map = {
        "A in": "dip8",
        "B in": "dip8",
        "Control": "dip_or_tie",
        "Y out": "led8",
    }
    for title, nets in _IO_SECTIONS:
        section_nets = [n for n in nets if n in defined]
        if section_nets:
            sections.append(
                IoSectionSpec(name=title, part=part_map.get(title, "signal"), nets=list(section_nets))
            )
    return sections


def reorder_section_nets(
    section: IoSectionSpec,
    anchors: list[PinAnchor],
    *,
    preserve_bus_order: bool = True,
) -> IoSectionSpec:
    """Sort panel nets by connected IC pin Y coordinate."""
    net_y: dict[str, float] = {}
    for a in anchors:
        if a.package_id == ASSEMBLY_IO_PANEL_PKG:
            continue
        if a.net in section.nets:
            net_y[a.net] = net_y.get(a.net, a.y)

    def sort_key(net: str) -> tuple[float, str]:
        if net in net_y:
            return (net_y[net], net)
        # extract bit index for bus nets
        if preserve_bus_order and net[-1].isdigit():
            tail = net.rstrip("0123456789")
            try:
                idx = int(net[len(tail) :])
                return (float(idx), net)
            except ValueError:
                pass
        return (1e6, net)

    ordered = sorted(section.nets, key=sort_key)
    return IoSectionSpec(name=section.name, part=section.part, nets=ordered)


def optimize_io_panel(
    nl: Netlist,
    side: str,
    anchors: list[PinAnchor],
    *,
    canvas_width: float = 1200.0,
) -> IoPanelSpec:
    sections = default_io_sections(nl)
    reordered = [reorder_section_nets(s, anchors) for s in sections]
    return IoPanelSpec(side=side, sections=reordered, canvas_width=canvas_width)


def build_io_panel_anchors(
    nl: Netlist,
    panel: IoPanelSpec,
    *,
    layout: dict,
) -> tuple[list[PinAnchor], dict[str, float]]:
    margin = float(layout.get("margin", 180))
    panel_width = float(layout.get("io_panel_width", 128))
    lane_inset = float(layout.get("io_lane_inset", 12))
    lane_step = float(layout.get("io_lane_step", 5.25))
    row_pitch = 13.0
    section_gap = 8.0

    canvas_w = panel.canvas_width
    if panel.side == "right":
        panel_w = panel_width - 20.0
        x0 = canvas_w - panel_w - IO_PANEL_EDGE_MARGIN
        anchor_x = x0 + 8.0
        pin_side = "left"
        lane_base = x0 - lane_inset
        lane_dir = -1
    else:
        x0 = 14.0
        panel_w = panel_width - x0 - 6.0
        anchor_x = x0 + panel_w - 8.0
        pin_side = "right"
        lane_base = panel_width + lane_inset
        lane_dir = 1

    y = margin + 54.0
    panel_by_net: dict[str, PinAnchor] = {}
    panel_lane_x: dict[str, float] = {}
    lane_idx = 0

    for section in panel.sections:
        y += section_gap + 4.0
        for net in section.nets:
            panel_by_net[net] = PinAnchor(
                package_id=ASSEMBLY_IO_PANEL_PKG,
                dip_pin=0,
                logical_pin=net.removeprefix("net_"),
                net=net,
                x=anchor_x,
                y=y,
                side=pin_side,
            )
            panel_lane_x[net] = lane_base + lane_dir * lane_idx * lane_step
            lane_idx += 1
            y += row_pitch
        y += section_gap

    return list(panel_by_net.values()), panel_lane_x


def build_io_panel_schematic(
    panel: IoPanelSpec,
    nl: Netlist,
    *,
    margin: float,
    panel_width: float,
    lane_inset: float,
    lane_step: float,
    canvas_width: float,
) -> tuple[dict[str, PinAnchor], dict[str, float], list[str], float]:
    """Schematic I/O strip with configurable side and net order."""
    row_pitch = 13.0
    section_gap = 8.0
    y = margin + 54.0
    y_top = y - 6.0

    if panel.side == "right":
        panel_w = panel_width - 20.0
        x0 = canvas_width - panel_w - IO_PANEL_EDGE_MARGIN
        anchor_x = x0 + 8.0
        pin_side = "left"
        lane_base = x0 - lane_inset
        lane_dir = -1
        label_anchor = "start"
        label_x_off = 10.0
    else:
        x0 = 14.0
        panel_w = panel_width - x0 - 6.0
        anchor_x = x0 + panel_w - 8.0
        pin_side = "right"
        lane_base = panel_width + lane_inset
        lane_dir = 1
        label_anchor = "end"
        label_x_off = -8.0

    panel_by_net: dict[str, PinAnchor] = {}
    panel_lane_x: dict[str, float] = {}
    row_elems: list[str] = []
    lane_idx = 0

    for section in panel.sections:
        row_elems.append(
            f'<text x="{x0 + 4:.1f}" y="{y + 3:.1f}" class="io-section">'
            f"{section.name}</text>"
        )
        y += section_gap + 4.0
        for net in section.nets:
            color = "#d29922" if _is_control_net(net) else _net_color(net)
            short = net.removeprefix("net_")
            row_elems.append(
                f'<g class="io-row" data-net="{net}">'
                f'<text x="{anchor_x + label_x_off:.1f}" y="{y + 3:.1f}" text-anchor="{label_anchor}" '
                f'class="io-net-label">{short}</text>'
                f'<circle class="net-hub io-hub" data-net="{net}" '
                f'cx="{anchor_x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" opacity="0.95"/>'
                f"</g>"
            )
            panel_by_net[net] = PinAnchor(
                package_id=ASSEMBLY_IO_PANEL_PKG,
                dip_pin=0,
                logical_pin=short,
                net=net,
                x=anchor_x,
                y=y,
                side=pin_side,
            )
            panel_lane_x[net] = lane_base + lane_dir * lane_idx * lane_step
            lane_idx += 1
            y += row_pitch
        y += section_gap

    y_bottom = y + 4.0
    panel_elems = [
        f'<rect x="{x0:.1f}" y="{y_top:.1f}" width="{panel_w:.1f}" '
        f'height="{y_bottom - y_top:.1f}" rx="4" fill="#161b22" stroke="#30363d" '
        f'stroke-width="1"/>',
        f'<text x="{x0 + panel_w / 2:.1f}" y="{y_top + 11:.1f}" text-anchor="middle" '
        f'class="io-title">External I/O ({panel.side})</text>',
        *row_elems,
    ]
    return panel_by_net, panel_lane_x, panel_elems, y_bottom


def panel_svg_elements(panel: IoPanelSpec, layout: dict) -> list[str]:
    """Minimal SVG labels for board layout export."""
    margin = float(layout.get("margin", 180))
    panel_width = float(layout.get("io_panel_width", 128))
    row_pitch = 13.0
    section_gap = 8.0
    x0 = 14.0 if panel.side == "left" else panel.canvas_width - (panel_width - 20.0) - IO_PANEL_EDGE_MARGIN
    y = margin + 54.0
    elems = [
        f'<rect x="{x0:.1f}" y="{y - 6:.1f}" width="{panel_width - 20:.1f}" '
        f'height="200" rx="4" fill="#161b22" stroke="#30363d" opacity="0.9"/>',
        f'<text x="{x0 + (panel_width - 20) / 2:.1f}" y="{y + 4:.1f}" '
        f'text-anchor="middle" fill="#8b949e" font-size="10">I/O ({panel.side})</text>',
    ]
    for section in panel.sections:
        y += section_gap + 4
        elems.append(
            f'<text x="{x0 + 4:.1f}" y="{y:.1f}" fill="#c9d1d9" font-size="9">{section.name}</text>'
        )
        y += 10
        for net in section.nets:
            color = "#d29922" if _is_control_net(net) else _net_color(net)
            elems.append(
                f'<circle cx="{x0 + panel_width - 28:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
                f'<text x="{x0 + 6:.1f}" y="{y + 3:.1f}" fill="#8b949e" font-size="8">'
                f'{net.removeprefix("net_")}</text>'
            )
            y += row_pitch
        y += section_gap
    return elems
