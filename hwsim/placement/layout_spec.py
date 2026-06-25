"""Layout result dataclasses and YAML serialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from hwsim.placement.io_panel import IoPanelSpec, IoSectionSpec


@dataclass
class BoardPlacement:
    block: int = 0
    row: int = 0
    col: int = 0
    notch: str = "up"


@dataclass
class PackageLayout:
    abstract_x_mm: float = 0.0
    abstract_y_mm: float = 0.0
    mb102: BoardPlacement | None = None
    perfboard: BoardPlacement | None = None


@dataclass
class VariantLayout:
    io_panel: IoPanelSpec
    packages: dict[str, PackageLayout] = field(default_factory=dict)
    gate_assign: dict[str, dict[str, dict[str, str]]] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    positions_px: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class LayoutDocument:
    version: int = 1
    block: str = ""
    source: str = ""
    mode: str = "assembly"
    variants: dict[str, VariantLayout] = field(default_factory=dict)


def _section_to_yaml(s: IoSectionSpec) -> dict:
    return {"name": s.name, "part": s.part, "nets": s.nets}


def _section_from_yaml(d: dict) -> IoSectionSpec:
    return IoSectionSpec(name=d["name"], part=d.get("part", "signal"), nets=list(d.get("nets", [])))


def layout_to_yaml(doc: LayoutDocument) -> str:
    data: dict[str, Any] = {
        "version": doc.version,
        "block": doc.block,
        "source": doc.source,
        "mode": doc.mode,
        "variants": {},
    }
    for vname, var in doc.variants.items():
        vdata: dict[str, Any] = {
            "io_panel": {
                "side": var.io_panel.side,
                "sections": [_section_to_yaml(s) for s in var.io_panel.sections],
            },
            "packages": {},
            "gate_assign": var.gate_assign,
            "metrics": var.metrics,
        }
        for pid, pl in var.packages.items():
            pdata: dict[str, Any] = {
                "abstract": {
                    "x_mm": round(pl.abstract_x_mm, 2),
                    "y_mm": round(pl.abstract_y_mm, 2),
                },
            }
            if pl.mb102:
                pdata["mb102"] = {
                    "block": pl.mb102.block,
                    "anchor_row": pl.mb102.row,
                    "anchor_col": pl.mb102.col,
                    "notch": pl.mb102.notch,
                }
            if pl.perfboard:
                pdata["perfboard"] = {
                    "row": pl.perfboard.row,
                    "col": pl.perfboard.col,
                    "notch": pl.perfboard.notch,
                }
            vdata["packages"][pid] = pdata
        data["variants"][vname] = vdata
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def layout_from_yaml(text: str) -> LayoutDocument:
    data = yaml.safe_load(text)
    doc = LayoutDocument(
        version=int(data.get("version", 1)),
        block=str(data.get("block", "")),
        source=str(data.get("source", "")),
        mode=str(data.get("mode", "assembly")),
    )
    for vname, vdata in (data.get("variants") or {}).items():
        io = vdata.get("io_panel", {})
        sections = [_section_from_yaml(s) for s in io.get("sections", [])]
        var = VariantLayout(
            io_panel=IoPanelSpec(side=io.get("side", "left"), sections=sections),
            gate_assign=dict(vdata.get("gate_assign", {})),
            metrics=dict(vdata.get("metrics", {})),
        )
        for pid, pdata in (vdata.get("packages") or {}).items():
            ab = pdata.get("abstract", {})
            pl = PackageLayout(
                abstract_x_mm=float(ab.get("x_mm", 0)),
                abstract_y_mm=float(ab.get("y_mm", 0)),
            )
            if "mb102" in pdata:
                m = pdata["mb102"]
                pl.mb102 = BoardPlacement(
                    block=int(m.get("block", 0)),
                    row=int(m.get("anchor_row", m.get("row", 0))),
                    col=int(m.get("anchor_col", m.get("col", 0))),
                    notch=str(m.get("notch", "up")),
                )
            if "perfboard" in pdata:
                p = pdata["perfboard"]
                pl.perfboard = BoardPlacement(
                    row=int(p.get("row", 0)),
                    col=int(p.get("col", 0)),
                    notch=str(p.get("notch", "up")),
                )
            var.packages[pid] = pl
        doc.variants[vname] = var
    return doc
