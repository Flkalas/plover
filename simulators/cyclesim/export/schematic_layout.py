"""KiCad-style schematic layout and SVG export for cyclesim functional blocks."""

from __future__ import annotations

from typing import Any

from simulators.cyclesim.export.schematic.alu8_template import (
    ORPHAN_PORTS,
    Alu8Template,
    build_alu8_template,
    chip_obstacles,
    port_anchor_x,
    port_label_positions,
)
from simulators.cyclesim.export.schematic.render import (
    render_global_label,
    render_grid,
    render_symbol,
    render_wires,
    svg_styles,
)
from simulators.cyclesim.export.schematic.router import (
    build_route_assignments,
    paths_hit_obstacles,
    route_all,
)
from simulators.cyclesim.export.schematic.symbols import place_instances
from simulators.cyclesim.export.schematic.types import PinAnchor, SchematicLayout

PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"
MARGIN = 100.0

# Re-export for tests and backward compatibility.
PinAnchor = PinAnchor
SchematicLayout = SchematicLayout


def _get_tmpl() -> Alu8Template:
    return build_alu8_template()


def layout_alu8_schematic(
    netlist: dict[str, Any],
    *,
    port_names: set[str] | None = None,
) -> SchematicLayout:
    tmpl = _get_tmpl()
    placed, anchors = place_instances(netlist, tmpl)
    ports = port_names or set()

    labels = port_label_positions(tmpl, ports)
    for net, (lx, ly, side) in labels.items():
        ax = port_anchor_x(side, tmpl)
        anchors.append(PinAnchor(ref="__port__", pin="", net=net, x=ax, y=ly, side=side))

    max_x = tmpl.right_io + MARGIN
    max_y = tmpl.height
    for inst in placed:
        max_x = max(max_x, inst["x"] + inst["w"] + MARGIN)
        max_y = max(max_y, inst["y"] + inst["h"] + MARGIN)

    return SchematicLayout(
        width=max_x,
        height=max_y,
        anchors=anchors,
        instances=placed,
        template=tmpl,
    )


def _route_bounds(
    layout: SchematicLayout,
    routes: dict[str, list[list[tuple[float, float]]]],
    port_labels: dict[str, tuple[float, float, str]],
) -> tuple[float, float, float, float]:
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    def grow(x: float, y: float) -> None:
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    for inst in layout.instances:
        grow(inst["x"], inst["y"])
        grow(inst["x"] + inst["w"], inst["y"] + inst["h"])

    for x, y, _side in port_labels.values():
        grow(x - 40, y - 20)
        grow(x + 40, y + 20)

    for paths in routes.values():
        for path in paths:
            for x, y in path:
                grow(x, y)

    pad = MARGIN
    return min_x - pad, min_y - pad, max_x + pad, max_y + pad


def render_alu8_schematic_svg(
    netlist: dict[str, Any],
    *,
    port_names: set[str] | None = None,
) -> tuple[str, float, float]:
    layout = layout_alu8_schematic(netlist, port_names=port_names)
    tmpl: Alu8Template = layout.template or _get_tmpl()
    ports = port_names or set()
    port_labels = port_label_positions(tmpl, ports)

    by_net: dict[str, list[PinAnchor]] = {}
    for anchor in layout.anchors:
        by_net.setdefault(anchor.net, []).append(anchor)

    routes = route_all(by_net, tmpl, layout.instances, ports)
    _, bus_rails, _, _ = build_route_assignments(by_net, tmpl, ports)

    wire_svg = render_wires(routes, bus_rails)
    sym_svg = "\n".join(render_symbol(inst, tmpl) for inst in layout.instances)
    label_svg = "\n".join(
        render_global_label(net, x, y, side, dashed=(net in ORPHAN_PORTS))
        for net, (x, y, side) in port_labels.items()
    )

    min_x, min_y, max_x, max_y = _route_bounds(layout, routes, port_labels)
    width = max_x - min_x
    height = max_y - min_y

    power_svg = ""
    if any(n["name"] in (PWR_VCC, PWR_GND) for n in netlist.get("nets", [])):
        power_svg = (
            f'<line class="pwr-rail" x1="{min_x + MARGIN:.1f}" y1="{min_y + MARGIN - 12:.1f}" '
            f'x2="{max_x - MARGIN:.1f}" y2="{min_y + MARGIN - 12:.1f}" '
            f'stroke="#f85149" stroke-width="1" opacity="0.4"/>'
            f'<text class="lbl-pwr" x="{min_x + MARGIN:.1f}" y="{min_y + MARGIN - 16:.1f}" fill="#f85149">VCC</text>'
            f'<line class="pwr-rail" x1="{min_x + MARGIN:.1f}" y1="{max_y - MARGIN + 12:.1f}" '
            f'x2="{max_x - MARGIN:.1f}" y2="{max_y - MARGIN + 12:.1f}" '
            f'stroke="#8b949e" stroke-width="1" opacity="0.4"/>'
            f'<text class="lbl-pwr" x="{min_x + MARGIN:.1f}" y="{max_y - MARGIN + 24:.1f}" fill="#8b949e">GND</text>'
        )

    grid_svg = render_grid(min_x, min_y, max_x, max_y)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x:.0f} {min_y:.0f} {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">'
        f"<style>{svg_styles()}</style>"
        f'<rect width="100%" height="100%" fill="#0d1117"/>'
        f"{grid_svg}"
        f"{power_svg}"
        f"{wire_svg}"
        f"{sym_svg}"
        f"{label_svg}"
        f"</svg>"
    )
    return svg, width, height


def collect_routed_segments(
    layout: SchematicLayout,
    *,
    port_names: set[str] | None = None,
) -> tuple[dict[float, set[str]], dict[float, set[str]]]:
    tmpl: Alu8Template = layout.template or _get_tmpl()
    ports = port_names or set()
    by_net: dict[str, list[PinAnchor]] = {}
    for anchor in layout.anchors:
        by_net.setdefault(anchor.net, []).append(anchor)

    routes = route_all(by_net, tmpl, layout.instances, ports)
    horiz: dict[float, set[str]] = {}
    vert: dict[float, set[str]] = {}
    for net, paths in routes.items():
        for path in paths:
            if len(path) < 2:
                continue
            for i in range(len(path) - 1):
                x0, y0 = path[i]
                x1, y1 = path[i + 1]
                if y0 == y1:
                    horiz.setdefault(y0, set()).add(net)
                if x0 == x1:
                    vert.setdefault(x0, set()).add(net)
    return horiz, vert


def net_anchor_map(layout: SchematicLayout) -> dict[str, list[PinAnchor]]:
    out: dict[str, list[PinAnchor]] = {}
    for a in layout.anchors:
        out.setdefault(a.net, []).append(a)
    return out


def collect_all_routes(
    layout: SchematicLayout,
    port_names: set[str] | None = None,
) -> dict[str, list[list[tuple[float, float]]]]:
    tmpl: Alu8Template = layout.template or _get_tmpl()
    ports = port_names or set()
    by_net: dict[str, list[PinAnchor]] = {}
    for anchor in layout.anchors:
        by_net.setdefault(anchor.net, []).append(anchor)
    return route_all(by_net, tmpl, layout.instances, ports)


def wires_avoid_chips(layout: SchematicLayout, port_names: set[str] | None = None) -> bool:
    routes = collect_all_routes(layout, port_names)
    obstacles = chip_obstacles(layout.instances)
    for paths in routes.values():
        if paths_hit_obstacles(paths, obstacles):
            return False
    return True
