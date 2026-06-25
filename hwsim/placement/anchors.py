"""Pin anchor geometry shared by cost model and schematic export."""

from __future__ import annotations

from hwsim.export_schematic import (
    ASSEMBLY_IO_PANEL_PKG,
    ASSEMBLY_LAYOUT,
    PhysicalPackage,
    PinAnchor,
    _package_dip_connections,
    _package_pin_count,
    _package_sort_key,
    _pinout_power_net,
    dip_pin_position,
    load_pinout,
)
from hwsim.netlist import Netlist
from hwsim.placement.io_panel import build_io_panel_anchors


def compute_default_positions(
    packages: list[PhysicalPackage],
    layout: dict,
    *,
    cols: int | None = None,
    assembly: bool = False,
) -> dict[str, tuple[float, float]]:
    cols = cols if cols is not None else int(layout["cols"])
    body_w = float(layout["body_w"])
    body_h = float(layout["body_h"])
    pin_len = float(layout["pin_len"])
    gap_x = float(layout["gap_x"])
    gap_y = float(layout["gap_y"])
    margin = float(layout["margin"])
    route_stub = float(layout["route_stub"])
    stub_step = float(layout.get("stub_step") or 0)
    pin_label_off = float(layout.get("pin_label_off", 6))
    use_stagger = bool(layout.get("stagger", False))
    stagger_frac = float(layout.get("stagger_frac", 0.5))
    stagger_y = float(layout.get("stagger_y", 0))
    io_panel_width = float(layout.get("io_panel_width", 128))
    io_corridor = float(layout.get("io_corridor", 72))
    io_chip_extra = float(layout.get("io_chip_extra", 0))

    pitch_x = body_w + gap_x
    pitch_y = body_h + gap_y
    stagger_x = pitch_x * stagger_frac if use_stagger else 0.0
    half_pins = 8
    fan_pad = pin_len + route_stub + max(0, half_pins - 1) * stub_step + pin_label_off + 12
    edge = max(margin, fan_pad)
    chip_edge = (
        (io_panel_width + io_corridor + io_chip_extra + fan_pad) if assembly else edge
    )

    sorted_pkgs = sorted(packages, key=_package_sort_key)
    positions: dict[str, tuple[float, float]] = {}
    for i, pkg in enumerate(sorted_pkgs):
        col = i % cols
        row = i // cols
        x_off = stagger_x if use_stagger and row % 2 == 1 else 0.0
        y_off = stagger_y if use_stagger and col % 2 == 1 else 0.0
        positions[pkg.id] = (
            chip_edge + col * pitch_x + x_off,
            margin + 48 + row * pitch_y + y_off,
        )
    return positions


def build_anchors(
    packages: list[PhysicalPackage],
    positions: dict[str, tuple[float, float]],
    pinouts: dict[str, dict] | None = None,
    *,
    layout: dict | None = None,
    io_panel: dict | None = None,
    nl: Netlist | None = None,
) -> tuple[list[PinAnchor], dict[str, float]]:
    """Build PinAnchor list for packages at given positions."""
    layout = layout or ASSEMBLY_LAYOUT
    pinouts = dict(pinouts or {})
    body_w = float(layout["body_w"])
    body_h = float(layout["body_h"])
    pin_len = float(layout["pin_len"])
    pin_pitch = layout.get("pin_pitch")

    anchors: list[PinAnchor] = []
    panel_lane_x: dict[str, float] = {}

    for pkg in packages:
        if pkg.part not in pinouts:
            try:
                pinouts[pkg.part] = load_pinout(pkg.part)
            except FileNotFoundError:
                pinouts[pkg.part] = {}
        po = pinouts[pkg.part]
        n_pins = _package_pin_count(pkg.part, po)
        bx, by = positions.get(pkg.id, (0.0, 0.0))
        dip_map = _package_dip_connections(pkg, po)

        for dip in range(1, n_pins + 1):
            px, py, side = dip_pin_position(
                dip,
                n_pins,
                bx,
                by,
                body_w,
                body_h,
                pin_len,
                pin_pitch=pin_pitch,
            )
            conns = dip_map.get(dip, [])
            if conns:
                seen: set[str] = set()
                for logical, net, _gate in conns:
                    if net in seen:
                        continue
                    seen.add(net)
                    anchors.append(
                        PinAnchor(
                            package_id=pkg.id,
                            dip_pin=dip,
                            logical_pin=logical,
                            net=net,
                            x=px,
                            y=py,
                            side=side,
                        )
                    )
            else:
                pwr = _pinout_power_net(dip, po)
                if pwr:
                    anchors.append(
                        PinAnchor(
                            package_id=pkg.id,
                            dip_pin=dip,
                            logical_pin="VCC" if pwr == "pwr_vcc" else "GND",
                            net=pwr,
                            x=px,
                            y=py,
                            side=side,
                        )
                    )

    if io_panel and nl is not None:
        panel_anchors, panel_lane_x = build_io_panel_anchors(nl, io_panel, layout=layout)
        anchors.extend(panel_anchors)

    return anchors, panel_lane_x
