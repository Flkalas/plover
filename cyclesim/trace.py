"""Phase-indexed waveform trace."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing import TYPE_CHECKING

from hwsim.netlist import Netlist

if TYPE_CHECKING:
    from cyclesim.engine import CycleContext

VALUE_NAMES = {0: "0", 1: "1", 2: "X", 3: "Z"}


@dataclass
class WaveTrace:
    samples: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def record_phase(self, ctx: "CycleContext", phase: int, nl: Netlist) -> None:
        probes = nl.probe_nets()
        for net in sorted(probes):
            v = ctx.get_net(net)
            rows = self.samples.setdefault(net, [])
            if rows and rows[-1].get("phase") == phase and rows[-1].get("v") == VALUE_NAMES.get(v, "?"):
                return
            rows.append({"phase": phase, "v": VALUE_NAMES.get(v, "?")})

    def to_json_dict(self) -> dict[str, list[dict[str, Any]]]:
        return dict(self.samples)
