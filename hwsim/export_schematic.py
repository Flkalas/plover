"""Export netlist as DIP package schematic SVG (pins + net wires)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from hwsim.netlist import Instance, Netlist
from hwsim.pinout import load_pinout

GATES_PER_CHIP: dict[str, int] = {
    "74HC04": 6,
    "74HC08": 4,
    "74HC32": 4,
    "74HC86": 4,
}

# Bring-up order for schematic layout (lower sorts first).
PART_LAYOUT_ORDER: dict[str, int] = {
    "74HC283": 10,
    "74HC04": 20,
    "74HC153": 30,
    "74HC157": 50,
    "ALU_CMP_SUB": 55,
}

# Behavioral-only — omitted from assembly schematic (12 physical DIP).
ALU8_ASSEMBLY_SKIP_REFS = frozenset(
    {"U_ALU_Y_MUX_SEL", "U_ALU_CMP_SUB", "U_ALU_INC_B_SEL", "U_ALU_INC_2C2"}
)

CONTROL_NET_PREFIXES = (
    "net_lgc",
    "net_153_s",
    "net_y_mux_sel",
    "net_bctrl",
    "net_inc_en",
    "net_cin",
    "net_cmp_z",
    "net_cmp_c_ge",
)

_ASSEMBLY_NOTE_ORPHAN = (
    "glue: INC_B_SEL + INC_2C2 + y_mux_sel + cmp from SUB — no extra DIP"
)

POWER_PINS = frozenset({"VCC", "VDD", "GND", "VSS"})
PWR_VCC = "pwr_vcc"
PWR_GND = "pwr_gnd"


@dataclass
class PhysicalPackage:
    id: str
    part: str
    instance_refs: list[str] = field(default_factory=list)
    # logical_pin, net_name, gate index 1-based (multi-gate ICs)
    connections: list[tuple[str, str, int | None]] = field(default_factory=list)


ROUTE_STUB = 32.0

ASSEMBLY_IO_PANEL_PKG = "__io_panel__"

ASSEMBLY_LAYOUT = {
    "cols": 3,
    "body_w": 72.0,
    "body_h": 100.0,
    "pin_len": 18.0,
    "gap_x": 156.0,
    "gap_y": 88.0,
    "margin": 40.0,
    "route_stub": ROUTE_STUB,
    "stub_step": 0,
    "pin_label_off": 6,
    "stagger": False,
    "io_panel_width": 128,
    "io_corridor": 72,
    "io_chip_extra": 0,
}

_IO_SECTIONS: list[tuple[str, list[str]]] = [
    ("A in", [f"net_a{i}" for i in range(8)]),
    ("B in", [f"net_b{i}" for i in range(8)]),
    (
        "Control",
        [
            "net_153_s0",
            "net_153_s1",
            "net_lgc3",
            "net_lgc2",
            "net_lgc1",
            "net_lgc0",
            "net_bctrl3",
            "net_bctrl2",
            "net_bctrl1",
            "net_bctrl0",
            "net_inc_en",
            "net_cin",
            "net_y_mux_sel",
        ],
    ),
    ("Y out", [f"net_y{i}" for i in range(8)] + ["net_cmp_c_ge", "net_cmp_z"]),
]


def _net_hub_center(pts: list[PinAnchor]) -> tuple[float, float]:
    if not pts:
        return 0.0, 0.0
    return sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts)


def _route_from_panel(
    px: float,
    py: float,
    hx: float,
    hy: float,
    *,
    stub: float = 32.0,
    lane_x: float | None = None,
    pin_side: str = "left",
) -> str:
    lane_x = (px + hx) / 2 if lane_x is None else lane_x
    ex = px - stub if pin_side == "left" else px + stub
    return (
        f"{px:.1f},{py:.1f} {ex:.1f},{py:.1f} {lane_x:.1f},{py:.1f} "
        f"{lane_x:.1f},{hy:.1f} {hx:.1f},{hy:.1f}"
    )


@dataclass
class PinAnchor:
    package_id: str
    dip_pin: int
    logical_pin: str
    net: str
    x: float
    y: float
    side: str  # "left" | "right" — wire exits away from chip body


def _normalize_net(pin: str, net: str) -> str:
    if pin in ("VCC", "VDD") or net in (PWR_VCC, "pwr_vcc"):
        return PWR_VCC
    if pin in ("GND", "VSS") or net in (PWR_GND, "pwr_gnd"):
        return PWR_GND
    return net


def _skip_connection(pin: str, net: str) -> bool:
    """Drop non-power nets that are not modeled (only VCC/GND rails kept)."""
    if pin in POWER_PINS:
        return False
    if net in (PWR_VCC, PWR_GND):
        return False
    return net.startswith("pwr_")


def _is_power_rail(net: str) -> bool:
    return net in (PWR_VCC, PWR_GND)


def _pin_visual(logical: str, net: str) -> tuple[str, str]:
    """fill, stroke (signal vs power color)."""
    if net == PWR_VCC or logical in ("VCC", "VDD"):
        return "#f85149", "#0d1117"
    if net == PWR_GND or logical in ("GND", "VSS"):
        return "#6e7681", "#e6edf3"
    return "#3fb950", "#0d1117"


def _pin_num(key: str | int) -> int:
    return int(str(key).strip("\"'"))


def _instance_index(ref: str) -> int | None:
    """Trailing digit suffix: U_ALU_86_INV_3 -> 3, U_ALU_04_N7 -> 7."""
    m = re.search(r"(\d+)$", ref)
    if not m:
        return None
    tail = m.group(1)
    # Exclude refs that end in a part code like 283_LO (no pure numeric tail)
    if len(tail) > 2 and tail.startswith("0"):
        return None
    return int(tail)


def _instance_base(ref: str, idx: int) -> str:
    return ref[: -len(str(idx))]


def _package_sort_key(pkg: PhysicalPackage) -> tuple[int, int, str]:
    part_rank = PART_LAYOUT_ORDER.get(pkg.part, 500)
    m = re.search(r"(\d+)$", pkg.id)
    num = int(m.group(1)) if m else 0
    return (part_rank, num, pkg.id)


def _is_control_net(net: str) -> bool:
    return any(net == p or net.startswith(p) for p in CONTROL_NET_PREFIXES)


def _group_alu8_assembly(instances: list[Instance]) -> list[PhysicalPackage]:
    """12 DIP packages — Gigatron bit-slice 153×8 (glue skipped)."""
    filtered = [i for i in instances if i.ref not in ALU8_ASSEMBLY_SKIP_REFS]
    return _group_logical(filtered)


def group_into_packages(
    instances: list[Instance], *, assembly: bool = False
) -> list[PhysicalPackage]:
    if assembly:
        return _group_alu8_assembly(instances)
    return _group_logical(instances)


def _group_logical(instances: list[Instance]) -> list[PhysicalPackage]:
    singles: dict[str, PhysicalPackage] = {}
    multi: dict[tuple[str, int], PhysicalPackage] = {}

    for inst in instances:
        gpc = GATES_PER_CHIP.get(inst.part)
        if not gpc:
            pkg = PhysicalPackage(id=inst.ref, part=inst.part, instance_refs=[inst.ref])
            for pin, net in inst.pins.items():
                if not _skip_connection(pin, net):
                    pkg.connections.append((pin, _normalize_net(pin, net), None))
            singles[inst.ref] = pkg
            continue

        idx = _instance_index(inst.ref)
        if idx is None:
            pkg = PhysicalPackage(id=inst.ref, part=inst.part, instance_refs=[inst.ref])
            for pin, net in inst.pins.items():
                if not _skip_connection(pin, net):
                    pkg.connections.append((pin, _normalize_net(pin, net), 1))
            singles[inst.ref] = pkg
            continue

        base = _instance_base(inst.ref, idx)
        pkg_idx = idx // gpc
        gate = (idx % gpc) + 1
        key = (base, pkg_idx)
        if key not in multi:
            suffix = f"#{pkg_idx + 1}" if pkg_idx else ""
            multi[key] = PhysicalPackage(
                id=f"{base}{suffix}",
                part=inst.part,
            )
        pkg = multi[key]
        pkg.instance_refs.append(inst.ref)
        for pin, net in inst.pins.items():
            if not _skip_connection(pin, net):
                pkg.connections.append((pin, _normalize_net(pin, net), gate))

    return list(singles.values()) + list(multi.values())


def _logical_to_dip_pin(
    logical: str, gate_1based: int | None, pinout: dict
) -> int | None:
    plover = pinout.get("plover_netlist")
    if isinstance(plover, dict):
        m = plover.get("map")
        if isinstance(m, dict) and logical in m:
            entry = m[logical]
            if isinstance(entry, dict) and "dip" in entry:
                return int(entry["dip"])

    gates = pinout.get("gates")
    if isinstance(gates, dict) and gate_1based is not None:
        g = gates.get(str(gate_1based))
        if isinstance(g, dict) and logical in g:
            return int(g[logical])

    pins = pinout.get("pins", {})
    if isinstance(pins, dict):
        for num, ent in pins.items():
            if not isinstance(ent, dict):
                continue
            if ent.get("sym") == logical:
                return _pin_num(num)
            aliases = ent.get("aliases", [])
            if isinstance(aliases, list) and logical in aliases:
                return _pin_num(num)
            # 1A style for gate-specific sym
            if gate_1based and ent.get("sym") == f"{gate_1based}{logical}":
                return _pin_num(num)
    return None


def _package_pin_count(part: str, pinout: dict) -> int:
    pkg = pinout.get("package", {})
    if isinstance(pkg, dict) and "pins" in pkg:
        return int(pkg["pins"])
    pins = pinout.get("pins", {})
    if isinstance(pins, dict):
        return len(pins)
    return 16


def _pinout_power_net(dip: int, pinout: dict) -> str | None:
    pins = pinout.get("pins", {})
    if not isinstance(pins, dict):
        return None
    ent = pins.get(str(dip))
    if not isinstance(ent, dict):
        return None
    sym = str(ent.get("sym", ""))
    if sym in ("VCC", "VDD"):
        return PWR_VCC
    if sym in ("GND", "VSS"):
        return PWR_GND
    return None


def _package_dip_connections(
    pkg: PhysicalPackage,
    pinout: dict,
) -> dict[int, list[tuple[str, str, int | None]]]:
    out: dict[int, list[tuple[str, str, int | None]]] = {}
    for logical, net, gate in pkg.connections:
        dip = _logical_to_dip_pin(logical, gate, pinout)
        if dip is None:
            continue
        out.setdefault(dip, []).append((logical, net, gate))
    return out


def dip_pin_position(
    dip_pin: int,
    n_pins: int,
    body_x: float,
    body_y: float,
    body_w: float,
    body_h: float,
    pin_len: float = 16.0,
    *,
    pin_pitch: float | None = None,
) -> tuple[float, float, str]:
    """Pin 1 lower-left, notch up; left column 1..n/2 bottom-up, right top-down."""
    half = n_pins // 2
    if dip_pin <= half:
        i = dip_pin - 1
        y = body_y + body_h - (i + 0.5) * (body_h / half)
        return body_x - pin_len, y, "left"
    i = dip_pin - half - 1
    y = body_y + (i + 0.5) * (body_h / half)
    return body_x + body_w + pin_len, y, "right"


def _net_color(net: str) -> str:
    h = hashlib.md5(net.encode()).hexdigest()[:6]
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    # keep wires visible on dark bg
    r = 80 + (r * 175) // 255
    g = 100 + (g * 155) // 255
    b = 120 + (b * 135) // 255
    return f"#{r:02x}{g:02x}{b:02x}"


def _route_polyline(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    side: str,
    stub: float = ROUTE_STUB,
    *,
    dip_pin: int | None = None,
    n_pins: int = 16,
    stub_step: float = 0.0,
) -> str:
    """Exit horizontally from pin (left pins go left, right pins go right), then to hub."""
    extra = 0.0
    if dip_pin is not None and stub_step:
        half = max(n_pins // 2, 1)
        extra = ((dip_pin - 1) % half) * stub_step
    effective = stub + extra
    ex = x1 - effective if side == "left" else x1 + effective
    return f"{x1:.1f},{y1:.1f} {ex:.1f},{y1:.1f} {ex:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"


def _route_to_rail(
    px: float, py: float, rail_y: float, side: str, stub: float = ROUTE_STUB
) -> str:
    ex = px - stub if side == "left" else px + stub
    return f"{px:.1f},{py:.1f} {ex:.1f},{py:.1f} {ex:.1f},{rail_y:.1f}"


def _add_assembly_glue_hubs(
    anchors: list[PinAnchor],
    instances: list[Instance],
    *,
    margin: float,
) -> None:
    """Floating hubs for nets that had only behavioral drivers in hwsim."""
    y = margin + 64
    x = margin + 8
    for inst in instances:
        if inst.ref not in ALU8_ASSEMBLY_SKIP_REFS:
            continue
        dy = 0.0
        for pin, net in inst.pins.items():
            if _skip_connection(pin, net):
                continue
            net_n = _normalize_net(pin, net)
            anchors.append(
                PinAnchor(
                    package_id=f"glue:{inst.ref}",
                    dip_pin=0,
                    logical_pin=pin,
                    net=net_n,
                    x=x,
                    y=y + dy,
                    side="left",
                )
            )
            dy += 14.0
        x += 52.0


def export_schematic_svg(
    nl: Netlist,
    *,
    cols: int = 5,
    assembly: bool | None = None,
    layout_spec=None,
) -> str:
    if assembly is None:
        assembly = nl.block == "alu8"
    packages = group_into_packages(nl.instances, assembly=assembly)
    pinouts: dict[str, dict] = {}

    body_w, body_h = 72.0, 100.0
    pin_len = 18.0
    gap_x, gap_y = 156.0, 88.0
    margin = 40.0

    pitch_x = body_w + gap_x
    pitch_y = body_h + gap_y
    stagger_x = pitch_x / 2  # odd rows shift half column (brick / zigzag)

    positions: dict[str, tuple[float, float]] = {}
    sorted_pkgs = sorted(packages, key=_package_sort_key)
    if layout_spec is not None and getattr(layout_spec, "positions_px", None):
        for pkg in sorted_pkgs:
            pos = layout_spec.positions_px.get(pkg.id)
            if pos is not None:
                positions[pkg.id] = pos
    for i, pkg in enumerate(sorted_pkgs):
        if pkg.id in positions:
            continue
        col = i % cols
        row = i // cols
        x_off = stagger_x if row % 2 == 1 else 0.0
        positions[pkg.id] = (
            margin + col * pitch_x + x_off,
            margin + 36 + row * pitch_y,
        )

    rows = (len(sorted_pkgs) + cols - 1) // cols if sorted_pkgs else 1
    width = margin * 2 + (cols - 1) * pitch_x + body_w + stagger_x
    height = margin * 2 + 36 + rows * pitch_y
    if positions:
        max_x = max(x for x, _ in positions.values()) + body_w
        max_y = max(y for _, y in positions.values()) + body_h
        width = max(width, margin + max_x)
        height = max(height, margin + max_y)

    anchors: list[PinAnchor] = []
    chip_elems: list[str] = []

    for pkg in sorted_pkgs:
        if pkg.part not in pinouts:
            try:
                pinouts[pkg.part] = load_pinout(pkg.part)
            except FileNotFoundError:
                pinouts[pkg.part] = {}
        po = pinouts[pkg.part]
        n_pins = _package_pin_count(pkg.part, po)
        bx, by = positions[pkg.id]

        chip_elems.append(
            f'<g class="chip" data-id="{_esc(pkg.id)}" data-part="{_esc(pkg.part)}">'
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{body_w:.1f}" height="{body_h:.1f}" '
            f'rx="3" fill="#21262d" stroke="#484f58" stroke-width="1.5"/>'
            f'<circle cx="{bx + 4:.1f}" cy="{by + body_h - 4:.1f}" r="3" fill="#f85149"/>'
            f'<text x="{bx + body_w / 2:.1f}" y="{by + 14:.1f}" text-anchor="middle" '
            f'class="lbl-ref">{_esc(pkg.id)}</text>'
            f'<text x="{bx + body_w / 2:.1f}" y="{by + 28:.1f}" text-anchor="middle" '
            f'class="lbl-part">{_esc(pkg.part)}</text>'
        )

        drawn_dip: set[int] = set()
        for logical, net, gate in pkg.connections:
            dip = _logical_to_dip_pin(logical, gate, po)
            if dip is None:
                continue
            px, py, side = dip_pin_position(dip, n_pins, bx, by, body_w, body_h, pin_len)
            fill, stroke = _pin_visual(logical, net)
            if dip not in drawn_dip:
                drawn_dip.add(dip)
                chip_elems.append(
                    f'<circle class="pin" data-net="{_esc(net)}" data-pkg="{_esc(pkg.id)}" '
                    f'data-side="{_esc(side)}" '
                    f'cx="{px:.1f}" cy="{py:.1f}" r="3.5" '
                    f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
                    f'<text x="{px + (6 if side == "left" else -6):.1f}" y="{py + 3:.1f}" '
                    f'text-anchor="{"start" if side == "left" else "end"}" class="lbl-pin">'
                    f'{_esc(str(dip))}</text>'
                )
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

        chip_elems.append("</g>")

    if assembly:
        _add_assembly_glue_hubs(anchors, nl.instances, margin=margin)

    net_map: dict[str, list[PinAnchor]] = {}
    for a in anchors:
        net_map.setdefault(a.net, []).append(a)

    rail_vcc_y = 14.0
    rail_gnd_y = height - 10.0
    rail_elems: list[str] = [
        f'<line x1="0" y1="{rail_vcc_y:.1f}" x2="{width:.1f}" y2="{rail_vcc_y:.1f}" '
        f'stroke="#f85149" stroke-width="2.5" opacity="0.35"/>',
        f'<line x1="0" y1="{rail_gnd_y:.1f}" x2="{width:.1f}" y2="{rail_gnd_y:.1f}" '
        f'stroke="#6e7681" stroke-width="2.5" opacity="0.45"/>',
        f'<text x="{margin:.1f}" y="{rail_vcc_y - 3:.1f}" class="lbl-rail-vcc">'
        f"VCC (5V)</text>",
        f'<text x="{margin:.1f}" y="{rail_gnd_y + 11:.1f}" class="lbl-rail-gnd">GND</text>',
    ]

    wire_elems: list[str] = []
    signal_nets = 0
    for net, pts in sorted(net_map.items()):
        if _is_power_rail(net):
            color = "#f85149" if net == PWR_VCC else "#6e7681"
            rail_y = rail_vcc_y if net == PWR_VCC else rail_gnd_y
            wire_elems.append(f'<g class="net power" data-net="{_esc(net)}">')
            for p in pts:
                pts_attr = _route_to_rail(p.x, p.y, rail_y, p.side)
                wire_elems.append(
                    f'<polyline class="wire-hit" data-net="{_esc(net)}" '
                    f'data-pkg="{_esc(p.package_id)}" points="{pts_attr}"/>'
                    f'<polyline class="wire-seg" data-net="{_esc(net)}" '
                    f'data-pkg="{_esc(p.package_id)}" points="{pts_attr}" fill="none" '
                    f'stroke="{color}" stroke-width="1.5" opacity="0.75" '
                    f'pointer-events="none"/>'
                )
            wire_elems.append("</g>")
            continue

        if len(pts) < 1:
            continue
        if len(pts) < 2:
            p = pts[0]
            signal_nets += 1
            color = "#d29922" if _is_control_net(net) else _net_color(net)
            wire_elems.append(
                f'<g class="net orphan" data-net="{_esc(net)}">'
                f'<circle class="net-hub" data-net="{_esc(net)}" cx="{p.x:.1f}" cy="{p.y:.1f}" '
                f'r="3" fill="{color}" opacity="0.9"/>'
                f'<text class="net-label lbl-net" data-net="{_esc(net)}" '
                f'x="{p.x:.1f}" y="{p.y - 6:.1f}" text-anchor="middle">{_esc(net)}</text>'
                f"</g>"
            )
            continue
        signal_nets += 1
        color = "#d29922" if _is_control_net(net) else _net_color(net)
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        wire_elems.append(
            f'<g class="net" data-net="{_esc(net)}">'
            f'<circle class="net-hub" data-net="{_esc(net)}" cx="{cx:.1f}" cy="{cy:.1f}" '
            f'r="3" fill="{color}" opacity="0.9"/>'
        )
        for p in pts:
            pts_attr = _route_polyline(p.x, p.y, cx, cy, p.side)
            wire_elems.append(
                f'<polyline class="wire-hit" data-net="{_esc(net)}" '
                f'data-pkg="{_esc(p.package_id)}" points="{pts_attr}"/>'
                f'<polyline class="wire-seg" data-net="{_esc(net)}" '
                f'data-pkg="{_esc(p.package_id)}" points="{pts_attr}" fill="none" '
                f'stroke="{color}" stroke-width="1.2" opacity="0.55" pointer-events="none"/>'
            )
        wire_elems.append(
            f'<text class="net-label lbl-net" data-net="{_esc(net)}" '
            f'x="{cx:.1f}" y="{cy - 6:.1f}" text-anchor="middle">'
            f'{_esc(net)}</text>'
        )
        wire_elems.append("</g>")

    vcc_count = len(net_map.get(PWR_VCC, []))
    gnd_count = len(net_map.get(PWR_GND, []))

    style = """
    svg{-webkit-user-select:none;user-select:none;-webkit-user-drag:none}
    text{font-family:system-ui,sans-serif;pointer-events:none;user-select:none}
    .lbl-ref{font-size:10px;font-weight:600;fill:#e6edf3}
    .lbl-part{font-size:9px;fill:#8b949e}
    .lbl-pin{font-size:8px;fill:#c9d1d9}
    .lbl-net{font-size:7px;fill:#8b949e}
    .lbl-rail-vcc{font-size:9px;font-weight:600;fill:#f85149}
    .lbl-rail-gnd{font-size:9px;font-weight:600;fill:#8b949e}
    .chip{cursor:grab}
    .chip rect:hover{stroke:#58a6ff}
    .chip.highlight rect{stroke:#58a6ff;stroke-width:2}
    .chip.selected rect{stroke:#f0883e;stroke-width:2.5}
    .net-hub.selected{stroke:#f0883e;stroke-width:2.5}
    .wire-seg.selected{stroke-width:3;opacity:1}
    .wire-handle.selected{opacity:1;stroke:#f0883e;stroke-width:2}
    .wire-seg{pointer-events:stroke;transition:opacity .12s,stroke-width .12s}
    .wire-hit{pointer-events:stroke;fill:none;stroke:transparent;stroke-width:18;cursor:move}
    .net-hub{transition:opacity .12s;cursor:move;stroke:none}
    .net-hub.selected{stroke:#f0883e;stroke-width:2.5}
    .wire-handle{fill:#58a6ff;stroke:#0d1117;stroke-width:1;cursor:move;opacity:0;transition:opacity .12s}
    .wire-handle.on{opacity:0.9}
    """

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'data-rail-vcc-y="{rail_vcc_y:.1f}" data-rail-gnd-y="{rail_gnd_y:.1f}">',
        f"<style>{style}</style>",
        f'<rect width="100%" height="100%" fill="#0d1117"/>',
        f'<text x="{margin:.0f}" y="{margin + 12:.0f}" class="lbl-part">'
        f"block: {_esc(nl.block)}"
        + (
            f" (assembly 12 DIP) | packages: {len(sorted_pkgs)} | "
            f"signals: {signal_nets} | control: orange | {_ASSEMBLY_NOTE_ORPHAN} | "
            f"VCC: {vcc_count} GND: {gnd_count}"
            if assembly
            else f" (hwsim logical) | packages: {len(sorted_pkgs)} | "
            f"signals: {signal_nets} | VCC: {vcc_count} GND: {gnd_count}"
        )
        + "</text>",
        '<g id="rails">',
        *rail_elems,
        "</g>",
        '<g id="wires">',
        *wire_elems,
        "</g>",
        '<g id="chips">',
        *chip_elems,
        "</g>",
        '<g id="wire-handles"></g>',
        "</svg>",
    ]
    return "\n".join(lines)


def _interactive_script() -> str:
    path = Path(__file__).resolve().parents[1] / "hw" / "viewer" / "schematic-interactive.js"
    return path.read_text(encoding="utf-8")


def export_schematic_html(svg: str, title: str = "Schematic") -> str:
    interactive_js = _interactive_script()
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(title)}</title>
  <style>
    html, body {{ margin: 0; height: 100%; background: #0d1117; overflow: hidden;
      -webkit-user-select: none; user-select: none; }}
    #wrap {{ width: 100%; height: 100%; overflow: auto; cursor: grab;
      -webkit-user-select: none; user-select: none; }}
    #stage, #stage svg {{ -webkit-user-select: none; user-select: none; }}
    #wrap:active {{ cursor: grabbing; }}
    #toolbar {{
      position: fixed; top: 8px; right: 8px; z-index: 10;
      background: #161b22; border: 1px solid #30363d; border-radius: 6px;
      padding: 6px 10px; font: 12px system-ui; color: #e6edf3;
    }}
    #toolbar button {{
      margin-left: 4px; padding: 4px 8px; cursor: pointer;
      background: #21262d; color: #e6edf3; border: 1px solid #484f58; border-radius: 4px;
    }}
    #stage {{ transform-origin: 0 0; }}
  </style>
</head>
<body>
  <div id="toolbar">
  <div>Click to select · drag chip/hub/wire · Esc clears · orange = control nets</div>
  <div id="sel-status" style="margin:4px 0 6px;font-size:11px;color:#8b949e">(nothing selected)</div>
  <div>
    <span style="opacity:.6;margin:0 8px">|</span>
    Zoom: <button type="button" id="zin">+</button>
    <button type="button" id="zout">-</button>
    <button type="button" id="zreset">100%</button>
  </div>
  </div>
  <div id="wrap">
    <div id="stage">{svg}</div>
  </div>
  <script>
    const stage = document.getElementById('stage');
    const wrap = document.getElementById('wrap');
    let scale = 1;
    function applyScale() {{
      stage.style.transform = 'scale(' + scale + ')';
    }}
    document.getElementById('zin').onclick = () => {{ scale *= 1.15; applyScale(); }};
    document.getElementById('zout').onclick = () => {{ scale /= 1.15; applyScale(); }};
    document.getElementById('zreset').onclick = () => {{ scale = 1; applyScale(); }};
    wrap.addEventListener('wheel', (e) => {{
      e.preventDefault();
      scale *= e.deltaY < 0 ? 1.08 : 1/1.08;
      applyScale();
    }}, {{ passive: false }});
  </script>
"""
    tail = """
  <script>
"""
    tail += interactive_js
    tail += """
    initSchematicInteractive(document.getElementById('stage'));
  </script>
</body>
</html>
"""
    return head + tail


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
