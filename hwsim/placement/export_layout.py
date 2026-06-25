"""Breadboard / perfboard layout SVG export."""

from __future__ import annotations

from hwsim.export_schematic import PhysicalPackage, _net_color, _package_sort_key
from hwsim.placement.boards.mb102 import PITCH_MM, px_to_mm, snap_dip_mb102
from hwsim.placement.boards.perfboard import snap_dip_perfboard
from hwsim.placement.io_panel import IoPanelSpec, panel_svg_elements
from hwsim.placement.layout_spec import BoardPlacement, PackageLayout, VariantLayout
from hwsim.pinout import load_pinout


def _wire_list_sidebar(net_lengths: dict[str, float], width: float) -> list[str]:
    sx = width - 180
    lines = [
        f'<rect x="{sx:.0f}" y="20" width="170" height="{max(200, 14 * min(20, len(net_lengths)) + 30):.0f}" '
        f'fill="#161b22" stroke="#30363d" rx="4"/>',
        f'<text x="{sx + 8:.0f}" y="38" fill="#c9d1d9" font-size="10" font-weight="bold">Wire list</text>',
    ]
    y = 52
    for net, mm in sorted(net_lengths.items(), key=lambda x: -x[1])[:20]:
        color = _net_color(net)
        lines.append(
            f'<text x="{sx + 8:.0f}" y="{y:.0f}" fill="{color}" font-size="8">'
            f'{net.removeprefix("net_")} {mm:.0f}mm</text>'
        )
        y += 12
    return lines


def export_board_svg(
    variant: VariantLayout,
    packages: list[PhysicalPackage],
    *,
    board: str,
    net_lengths: dict[str, float] | None = None,
    width: float = 1200.0,
    height: float = 900.0,
) -> str:
    pinouts: dict[str, dict] = {}
    elems: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">',
        '<rect width="100%" height="100%" fill="#0d1117"/>',
        f'<text x="20" y="24" fill="#c9d1d9" font-size="14">Plover layout ({board}) ??'
        f'I/O {variant.io_panel.side}</text>',
    ]

    # Grid dots
    pitch_px = PITCH_MM / 0.35
    for x in range(0, int(width), int(pitch_px * 5)):
        for y in range(40, int(height), int(pitch_px)):
            elems.append(f'<circle cx="{x}" cy="{y}" r="0.8" fill="#21262d"/>')

    io = variant.io_panel
    io.canvas_width = width
    elems.extend(panel_svg_elements(io, {"margin": 180, "io_panel_width": 128}))

    sorted_pkgs = sorted(packages, key=_package_sort_key)
    for pkg in sorted_pkgs:
        pl = variant.packages.get(pkg.id)
        pos = variant.positions_px.get(pkg.id)
        if pos:
            bx, by = pos
        elif pl:
            bx = pl.abstract_x_mm / 0.35
            by = pl.abstract_y_mm / 0.35
        else:
            continue

        if pkg.part not in pinouts:
            try:
                pinouts[pkg.part] = load_pinout(pkg.part)
            except FileNotFoundError:
                pinouts[pkg.part] = {}
        n_pins = int(pinouts[pkg.part].get("package", {}).get("pins", 16))
        bw = 84 if n_pins >= 16 else 72
        bh = 152 if n_pins >= 16 else 100

        elems.append(
            f'<g class="chip" data-id="{pkg.id}">'
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="{bh}" rx="3" '
            f'fill="#21262d" stroke="#58a6ff" stroke-width="1.5"/>'
            f'<circle cx="{bx + 4:.1f}" cy="{by + 4:.1f}" r="3" fill="#f85149"/>'
            f'<text x="{bx + bw/2:.1f}" y="{by + bh/2:.1f}" text-anchor="middle" '
            f'fill="#e6edf3" font-size="9">{pkg.id}</text>'
            f"</g>"
        )

        if pl and board == "mb102" and pl.mb102:
            elems.append(
                f'<text x="{bx:.1f}" y="{by - 6:.1f}" fill="#8b949e" font-size="7">'
                f'MB102 b{pl.mb102.block} r{pl.mb102.row} c{pl.mb102.col}</text>'
            )
        elif pl and board == "perfboard" and pl.perfboard:
            elems.append(
                f'<text x="{bx:.1f}" y="{by - 6:.1f}" fill="#8b949e" font-size="7">'
                f'perf r{pl.perfboard.row} c{pl.perfboard.col}</text>'
            )

    if net_lengths:
        elems.extend(_wire_list_sidebar(net_lengths, width))

    elems.append("</svg>")
    return "\n".join(elems)


def fill_board_coords(
    variant: VariantLayout,
    packages: list[PhysicalPackage],
    pinouts: dict[str, dict],
) -> None:
    """Populate mb102 / perfboard snap coords from abstract mm positions."""
    for pkg in packages:
        pl = variant.packages.setdefault(pkg.id, PackageLayout())
        pos = variant.positions_px.get(pkg.id)
        if not pos:
            continue
        x_mm, y_mm = px_to_mm(pos[0], pos[1])
        pl.abstract_x_mm = x_mm
        pl.abstract_y_mm = y_mm
        po = pinouts.get(pkg.part, {})
        n_pins = int(po.get("package", {}).get("pins", 16))
        mb = snap_dip_mb102(n_pins, x_mm, y_mm)
        pf = snap_dip_perfboard(n_pins, x_mm, y_mm)
        pl.mb102 = BoardPlacement(block=mb.block, row=mb.row, col=mb.col)
        pl.perfboard = BoardPlacement(row=pf.row, col=pf.col)
