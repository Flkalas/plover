"""Cycle-accurate chip models (no propagation delay)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cyclesim.engine import CycleContext

# 0=L, 1=H, 2=X, 3=Z
L, H, X, Z = 0, 1, 2, 3


class CycleModel(ABC):
    part: str = ""
    is_sequential: bool = False

    def __init__(self, ref: str, pin_nets: dict[str, str], ctx: CycleContext) -> None:
        self.ref = ref
        self.pin_nets = pin_nets
        self.ctx = ctx

    def net_for(self, pin: str) -> str:
        return self.pin_nets[pin]

    def read(self, pin: str) -> int:
        return self.ctx.get_net(self.net_for(pin))

    def read_bit(self, pin: str) -> int:
        return self.read(pin)

    def drive(self, pin: str, value: int) -> None:
        self.ctx.drive_net(self.net_for(pin), value, self.ref)

    @abstractmethod
    def eval_comb(self) -> bool:
        """Evaluate combinational outputs. Return True if any net driven changed."""
        ...

    def eval_clock(self, edge: str) -> bool:
        """posedge | negedge — default no-op."""
        return False
