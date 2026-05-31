"""Chip behavioral models for event-driven simulation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from hwsim.netlist import delay_ns

if TYPE_CHECKING:
    from hwsim.simulator import SimContext


class ChipModel(ABC):
    part: str = ""

    def __init__(self, ref: str, pin_nets: dict[str, str], ctx: SimContext) -> None:
        self.ref = ref
        self.pin_nets = pin_nets
        self.ctx = ctx
        self._prev_clk: dict[str, int] = {}

    def net_for(self, pin: str) -> str:
        return self.pin_nets[pin]

    def read(self, pin: str) -> int:
        net = self.net_for(pin)
        return self.ctx.get_net(net)

    def read_bit(self, pin: str) -> int:
        return self.read(pin) & 1

    def t_pd(self, part: str, *keys: str, default: int = 10) -> int:
        return delay_ns(self.ctx.timing, part, *keys, default=default)

    def on_net_change(self, net: str) -> None:
        pass

    @abstractmethod
    def on_start(self) -> None:
        ...

    def _drive(self, pin: str, value: int, delay: int, reason: str = "") -> None:
        net = self.net_for(pin)
        self.ctx.schedule_drive(net, value, delay, driver=self.ref, reason=reason)

    def _posedge(self, clk_pin: str) -> bool:
        net = self.net_for(clk_pin)
        cur = self.ctx.get_net(net) & 1
        prev = self._prev_clk.get(clk_pin, 0)
        self._prev_clk[clk_pin] = cur
        return prev == 0 and cur == 1


class Osc4M(ChipModel):
    part = "OSC_4M"

    def on_start(self) -> None:
        spec = self.ctx.timing.get("OSC_4M", {})
        freq = int(spec.get("frequency_hz", 4_000_000))
        half = max(1, 1_000_000_000 // (2 * freq))
        net = self.net_for("OUT")
        self.ctx.set_net_immediate(net, 0)
        self.ctx.wave.record(net, 0, 0)
        self.ctx.schedule_recurring_toggle(net, half, driver=self.ref)

    def on_net_change(self, net: str) -> None:
        pass


class Hc74Divider(ChipModel):
    """One DFF channel: posedge latch D -> Q, QN = ~Q."""

    part = "74HC74"
    channel: str = "1"

    def on_start(self) -> None:
        cp = f"{self.channel}CP"
        self._prev_clk[cp] = self.read_bit(cp)
        q_pin = f"{self.channel}Q"
        qn = f"{self.channel}QN"
        self._drive(q_pin, 0, 0, "init")
        self._drive(qn, 1, 0, "init")

    def on_net_change(self, net: str) -> None:
        cp = f"{self.channel}CP"
        if net != self.net_for(cp) and net != self.net_for(f"{self.channel}D"):
            return
        if not self._posedge(cp):
            return
        rd = self.read_bit(f"{self.channel}RD")
        sd = self.read_bit(f"{self.channel}SD")
        d = self.read_bit(f"{self.channel}D")
        t = self.t_pd("74HC74", "t_pd_q", default=15)
        q_pin = f"{self.channel}Q"
        qn = f"{self.channel}QN"
        if rd == 0:
            self._drive(q_pin, 0, t, "async clear")
            self._drive(qn, 1, t, "async clear")
            return
        if sd == 0:
            self._drive(q_pin, 1, t, "async preset")
            self._drive(qn, 0, t, "async preset")
            return
        if not self.ctx.check_setup(self.ref, cp, f"{self.channel}D", t):
            self._drive(q_pin, 2, t, "violation")  # X
            return
        self._drive(q_pin, d, t, "posedge")
        self._drive(qn, 1 - d, t, "posedge")


class Hc04(ChipModel):
    part = "74HC04"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        if net == self.net_for("A"):
            self._update()

    def _update(self) -> None:
        a = self.read_bit("A")
        if a > 1:
            return
        y = 1 - a
        t = self.t_pd("74HC04", "t_pd", default=9)
        self._drive("Y", y, t, "inv")


class Hc283(ChipModel):
    part = "74HC283"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        inputs = {self.net_for(f"A{i}") for i in range(4)}
        inputs |= {self.net_for(f"B{i}") for i in range(4)}
        inputs.add(self.net_for("C0"))
        if net in inputs:
            self._update()

    def _update(self) -> None:
        a = sum(self.read_bit(f"A{i}") << i for i in range(4))
        b = sum(self.read_bit(f"B{i}") << i for i in range(4))
        c0 = self.read_bit("C0")
        if any(self.read(f"A{i}") > 1 for i in range(4)):
            return
        if any(self.read(f"B{i}") > 1 for i in range(4)):
            return
        total = a + b + c0
        s = total & 0xF
        cout = (total >> 4) & 1
        t_sum = self.t_pd("74HC283", "t_pd", "sum", default=30)
        t_cout = self.t_pd("74HC283", "t_pd", "cout", default=30)
        for i in range(4):
            self._drive(f"S{i}", (s >> i) & 1, t_sum, "sum")
        self._drive("C4", cout, t_cout, "cout")


class Hc574(ChipModel):
    part = "74HC574"

    def on_start(self) -> None:
        self._prev_clk["CP"] = self.read_bit("CP")
        oe = self.read_bit("OE")
        if oe == 1:
            for i in range(8):
                self._drive(f"Q{i}", 3, 0, "high-z")  # Z

    def on_net_change(self, net: str) -> None:
        cp_net = self.net_for("CP")
        if net == cp_net or any(net == self.net_for(f"D{i}") for i in range(8)):
            if self._posedge("CP"):
                self._latch()
        if net == self.net_for("OE"):
            self._output_enable()

    def _latch(self) -> None:
        t = self.t_pd("74HC574", "t_pd_q", default=15)
        t_su = self.t_pd("74HC574", "t_setup", default=5)
        ok = True
        for i in range(8):
            if not self.ctx.check_setup(self.ref, "CP", f"D{i}", t_su):
                ok = False
                break
        if not ok:
            for i in range(8):
                self.ctx.latch_state[(self.ref, i)] = 2
            return
        for i in range(8):
            d = self.read_bit(f"D{i}")
            self.ctx.latch_state[(self.ref, i)] = d
        self._output_enable(delay=t)

    def _output_enable(self, delay: int = 0) -> None:
        oe = self.read_bit("OE")
        if oe == 1:
            for i in range(8):
                self._drive(f"Q{i}", 3, delay, "z")
            return
        for i in range(8):
            val = self.ctx.latch_state.get((self.ref, i), 0)
            self._drive(f"Q{i}", val, delay, "out")


class Hc161(ChipModel):
    part = "74HC161"

    def on_start(self) -> None:
        self._prev_clk["CP"] = self.read_bit("CP")
        for i in range(4):
            self._drive(f"Q{i}", 0, 0, "init")

    def on_net_change(self, net: str) -> None:
        if net != self.net_for("CP"):
            return
        if not self._posedge("CP"):
            return
        if self.read_bit("CEP") == 0 and self.read_bit("CET") == 0:
            return
        q = sum(self.read_bit(f"Q{i}") << i for i in range(4))
        q = (q + 1) & 0xF
        t = self.t_pd("74HC161", "t_clk_to_q", default=15)
        for i in range(4):
            self._drive(f"Q{i}", (q >> i) & 1, t, "count")


class Hc245(ChipModel):
    part = "74HC245"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        oe = self.read_bit("OE")
        dir_ = self.read_bit("DIR")
        if oe == 1:
            t = self.t_pd("74HC245", "t_pz", default=12)
            for i in range(8):
                self._drive(f"B{i}", 3, t, "z")
            return
        t = self.t_pd("74HC245", "t_pd", default=11)
        for i in range(8):
            src = f"A{i}" if dir_ else f"B{i}"
            dst = f"B{i}" if dir_ else f"A{i}"
            if src in self.pin_nets and dst in self.pin_nets:
                self._drive(dst, self.read_bit(src), t, "bus")


class Hc138(ChipModel):
    part = "74HC138"

    def on_start(self) -> None:
        self._decode()

    def on_net_change(self, net: str) -> None:
        self._decode()

    def _decode(self) -> None:
        if self.read_bit("E1") == 1 or self.read_bit("E2") == 1 or self.read_bit("E3") == 0:
            active = None
        else:
            a = sum(self.read_bit(f"A{i}") << i for i in range(3))
            active = a
        t = self.t_pd("74HC138", "t_pd", default=18)
        for i in range(8):
            y = 1 if active is None or active != i else 0
            self._drive(f"Y{i}", y, t, "decode")


class Hc08(ChipModel):
    part = "74HC08"

    def on_start(self) -> None:
        self._gate(lambda a, b: a & b)

    def on_net_change(self, net: str) -> None:
        self._gate(lambda a, b: a & b)

    def _gate(self, fn: Any) -> None:
        a, b = self.read_bit("A"), self.read_bit("B")
        if a > 1 or b > 1:
            return
        t = self.t_pd("74HC08", "t_pd", default=9)
        self._drive("Y", fn(a, b), t, "and")


class Hc32(Hc08):
    part = "74HC32"

    def on_start(self) -> None:
        self._gate(lambda a, b: a | b)

    def on_net_change(self, net: str) -> None:
        self._gate(lambda a, b: a | b)

    def _gate(self, fn: Any) -> None:
        a, b = self.read_bit("A"), self.read_bit("B")
        if a > 1 or b > 1:
            return
        t = self.t_pd("74HC32", "t_pd", default=9)
        self._drive("Y", fn(a, b), t, "or")


class Hc86(Hc08):
    part = "74HC86"

    def on_start(self) -> None:
        self._gate(lambda a, b: a ^ b)

    def on_net_change(self, net: str) -> None:
        self._gate(lambda a, b: a ^ b)

    def _gate(self, fn: Any) -> None:
        a = self.read_bit("A")
        b = self.read_bit("B")
        if a > 1 or b > 1:
            return
        t = self.t_pd("74HC86", "t_pd", default=9)
        self._drive("Y", fn(a, b), t, "xor")


def create_model(ref: str, part: str, pins: dict[str, str], ctx: SimContext) -> ChipModel:
    table: dict[str, type[ChipModel]] = {
        "OSC_4M": Osc4M,
        "74HC74": Hc74Divider,
        "74HC04": Hc04,
        "74HC283": Hc283,
        "74HC574": Hc574,
        "74HC161": Hc161,
        "74HC245": Hc245,
        "74HC138": Hc138,
        "74HC08": Hc08,
        "74HC32": Hc32,
        "74HC86": Hc86,
    }
    cls = table.get(part)
    if cls is None:
        raise ValueError(f"No model for part {part} ({ref})")
    return cls(ref, pins, ctx)
