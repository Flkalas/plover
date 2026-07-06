"""Zero-delay comb fixpoint + clock-edge sequential stepping."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from simulators.cyclesim.values import H, L, X, Z

FIXPOINT_LIMIT = 64


class Block(ABC):
    """Functional block in the cycle simulator."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def eval_comb(self, ctx: SimContext) -> bool:
        return False

    def tick(self, ctx: SimContext) -> None:
        pass


@dataclass
class SimContext:
    nets: dict[str, int] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
    clk: int = L
    violations: list[str] = field(default_factory=list)
    _pending: dict[str, tuple[int, str]] = field(default_factory=dict, repr=False)
    _stuck: set[str] = field(default_factory=set, repr=False)

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)

    def get(self, net: str, default: int = X) -> int:
        return self.nets.get(net, default)

    def set(self, net: str, value: int, *, stuck: bool = False) -> None:
        self.nets[net] = value
        if stuck:
            self._stuck.add(net)

    def drive(self, net: str, value: int, driver: str) -> bool:
        if net in self._stuck:
            return False
        prev = self._pending.get(net)
        if prev is not None and prev[0] != value and value not in (Z,) and prev[0] not in (Z,):
            self._pending[net] = (X, driver)
            return True
        self._pending[net] = (value, driver)
        return True

    def _flush_pending(self) -> bool:
        changed = False
        for net, (val, _drv) in self._pending.items():
            if net in self._stuck:
                continue
            if self.nets.get(net, X) != val:
                changed = True
            self.nets[net] = val
        self._pending.clear()
        return changed

    def reset_floats(self) -> None:
        for name in list(self.nets):
            if name not in self._stuck:
                self.nets[name] = X
        self._pending.clear()

    def clear_stuck(self) -> None:
        self._stuck.clear()

    def flush_pending(self) -> bool:
        return self._flush_pending()

    def comb_fixup(self) -> None:
        for _ in range(FIXPOINT_LIMIT):
            self._pending.clear()
            changed = False
            for block in self.blocks:
                if block.eval_comb(self):
                    changed = True
            if self._flush_pending():
                changed = True
            if not changed:
                return
        self.violations.append("comb fixpoint limit exceeded")

    def pulse_clock(self) -> None:
        self.clk = L
        self.comb_fixup()
        self.clk = H
        for block in self.blocks:
            block.tick(self)
        self.comb_fixup()
        self.clk = L
