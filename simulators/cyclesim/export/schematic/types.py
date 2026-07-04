"""Shared schematic layout types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PinSpec:
    name: str
    side: str  # left, right, top, bottom
    order: float


@dataclass
class PinAnchor:
    ref: str
    pin: str
    net: str
    x: float
    y: float
    side: str


@dataclass
class SchematicLayout:
    width: float
    height: float
    anchors: list[PinAnchor]
    instances: list[dict[str, Any]]
    template: Any = None
