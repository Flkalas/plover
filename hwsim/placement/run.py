"""Main layout optimization orchestrator."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from hwsim.export_schematic import ALU8_ASSEMBLY_SKIP_REFS, ASSEMBLY_LAYOUT
from hwsim.netlist import load_netlist
from hwsim.pinout import load_pinout
from hwsim.placement.anchors import build_anchors, compute_default_positions
from hwsim.placement.cost import layout_cost, net_lengths_mm
from hwsim.placement.export_layout import export_board_svg, fill_board_coords
from hwsim.placement.gate_assign import optimize_all_gate_assign
from hwsim.placement.graph import build_gate_units
from hwsim.placement.io_panel import optimize_io_panel
from hwsim.placement.layout_spec import LayoutDocument, PackageLayout, VariantLayout, layout_to_yaml
from hwsim.placement.optimizer import optimize_positions
from hwsim.placement.pack import (
    build_part_families,
    default_gate_assign,
    default_packages,
    merge_packages_with_assign,
)
from hwsim.placement.report import compute_variant_metrics, format_report, gate_move_summary


def _load_pinouts(packages) -> dict[str, dict]:
    pinouts: dict[str, dict] = {}
    for pkg in packages:
        if pkg.part not in pinouts:
            try:
                pinouts[pkg.part] = load_pinout(pkg.part)
            except FileNotFoundError:
                pinouts[pkg.part] = {}
    return pinouts


def _optimize_variant(
    nl,
    *,
    io_side: str,
    assembly: bool,
    seed: int,
    cols: int,
    sa_iterations: int = 120,
    snap_boards: bool = False,
) -> VariantLayout:
    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)
    base_pkgs = default_packages(nl, assembly=assembly)
    pinouts = _load_pinouts(base_pkgs)
    families = build_part_families(nl, units, base_pkgs, assembly=assembly)

    default_pos = compute_default_positions(
        base_pkgs, ASSEMBLY_LAYOUT, cols=cols, assembly=assembly
    )

    # SA on netlist-default packages; gate slots reassigned once after placement.
    packages = base_pkgs
    pinouts = _load_pinouts(packages)

    positions = optimize_positions(
        nl,
        packages,
        pinouts,
        io_side=io_side,
        cols=cols,
        seed=seed,
        iterations=sa_iterations,
    )

    gate_assign = optimize_all_gate_assign(
        families,
        units,
        positions,
        pinouts,
        seed=seed,
    )
    packages = merge_packages_with_assign(nl, gate_assign, units, assembly=assembly)

    anchors, lane_x = build_anchors(packages, positions, pinouts, layout=ASSEMBLY_LAYOUT, nl=nl)
    io_panel = optimize_io_panel(nl, io_side, anchors, canvas_width=1200.0)
    anchors, lane_x = build_anchors(
        packages,
        positions,
        pinouts,
        layout=ASSEMBLY_LAYOUT,
        io_panel=io_panel,
        nl=nl,
    )

    metrics = compute_variant_metrics(nl, anchors, panel_lane_x=lane_x)
    moves = gate_move_summary(nl, units, base_pkgs, gate_assign, assembly=assembly)
    metrics["gate_moves"] = moves

    pkg_layouts: dict[str, PackageLayout] = {}
    for pid, (x, y) in positions.items():
        x_mm, y_mm = x * 0.35, y * 0.35
        pkg_layouts[pid] = PackageLayout(abstract_x_mm=x_mm, abstract_y_mm=y_mm)

    var = VariantLayout(
        io_panel=io_panel,
        packages=pkg_layouts,
        gate_assign=gate_assign,
        metrics=metrics,
        positions_px=positions,
    )
    if snap_boards:
        fill_board_coords(var, packages, pinouts)
    return var


def optimize_layout(
    netlist_path: Path,
    *,
    assembly: bool = True,
    io_sides: tuple[str, ...] = ("left", "right"),
    seed: int = 0,
    cols: int = 3,
    sa_iterations: int = 120,
    snap_boards: bool = False,
) -> LayoutDocument:
    nl = load_netlist(netlist_path)
    doc = LayoutDocument(
        block=nl.block,
        source=str(netlist_path).replace("\\", "/"),
        mode="assembly" if assembly else "logical",
    )

    for side in io_sides:
        vname = f"io-{side}"
        doc.variants[vname] = _optimize_variant(
            nl,
            io_side=side,
            assembly=assembly,
            seed=seed,
            cols=cols,
            sa_iterations=sa_iterations,
            snap_boards=snap_boards,
        )

    return doc


def run_optimize_layout_cli(
    netlist_path: Path,
    *,
    output_yaml: Path | None = None,
    breadboard_svg: Path | None = None,
    perfboard_svg: Path | None = None,
    schematic_path: Path | None = None,
    html: bool = False,
    report: bool = False,
    assembly: bool = True,
    io_sides: str = "left,right",
    seed: int = 0,
    cols: int = 3,
    sa_iterations: int = 120,
    snap_boards: bool = False,
) -> LayoutDocument:
    sides = tuple(s.strip() for s in io_sides.split(",") if s.strip())

    doc = optimize_layout(
        netlist_path,
        assembly=assembly,
        io_sides=sides,
        seed=seed,
        cols=cols,
        sa_iterations=sa_iterations,
        snap_boards=snap_boards,
    )

    # Default baseline cost
    nl = load_netlist(netlist_path)
    base_pkgs = default_packages(nl, assembly=assembly)
    pinouts = _load_pinouts(base_pkgs)
    default_pos = compute_default_positions(base_pkgs, ASSEMBLY_LAYOUT, cols=cols, assembly=assembly)
    default_anchors, _ = build_anchors(base_pkgs, default_pos, pinouts, layout=ASSEMBLY_LAYOUT, nl=nl)
    default_cost = layout_cost(nl, default_anchors)

    if output_yaml:
        output_yaml.parent.mkdir(parents=True, exist_ok=True)
        output_yaml.write_text(layout_to_yaml(doc), encoding="utf-8")

    units = build_gate_units(nl, skip_refs=ALU8_ASSEMBLY_SKIP_REFS)

    for vname, var in doc.variants.items():
        packages = merge_packages_with_assign(
            nl, var.gate_assign, units, assembly=assembly
        )
        lengths = {}
        if var.metrics.get("top_nets"):
            for line in var.metrics.get("top_nets", []):
                parts = line.rsplit(" ", 1)
                if len(parts) == 2:
                    try:
                        lengths[f"net_{parts[0]}"] = float(parts[1].replace("mm", ""))
                    except ValueError:
                        pass

        suffix = f".{vname}"
        if snap_boards and breadboard_svg:
            out = _variant_path(breadboard_svg, suffix)
            out.parent.mkdir(parents=True, exist_ok=True)
            svg = export_board_svg(var, packages, board="mb102", net_lengths=lengths)
            out.write_text(svg, encoding="utf-8")

        if snap_boards and perfboard_svg:
            out = _variant_path(perfboard_svg, suffix)
            out.parent.mkdir(parents=True, exist_ok=True)
            svg = export_board_svg(var, packages, board="perfboard", net_lengths=lengths)
            out.write_text(svg, encoding="utf-8")

        if schematic_path:
            from hwsim.export_schematic import export_schematic_html, export_schematic_svg

            out = _variant_path(schematic_path, suffix)
            out.parent.mkdir(parents=True, exist_ok=True)
            svg = export_schematic_svg(nl, assembly=assembly, layout_spec=var)
            out.write_text(svg, encoding="utf-8")
            if html:
                html_out = out.with_suffix(".html")
                html_out.write_text(export_schematic_html(svg), encoding="utf-8")

    if report:
        text = format_report(
            nl,
            doc,
            default_cost=default_cost,
            units=units,
            packages=base_pkgs,
            assembly=assembly,
        )
        print(text)

    return doc


def _variant_path(base: Path, suffix: str) -> Path:
    """build/alu8.svg + .io-left -> build/alu8.io-left.svg"""
    stem = base.stem + suffix
    return base.with_name(stem + base.suffix)
