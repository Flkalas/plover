"""Combinational 74HC and ALU glue models."""

from __future__ import annotations

from typing import Any, Callable

from cyclesim.models.base import CycleModel, H, L, X, Z


class Hc04(CycleModel):
    part = "74HC04"

    def eval_comb(self) -> bool:
        a = self.read_bit("A")
        if a > 1:
            return False
        return self.ctx.drive_net(self.net_for("Y"), H if a == 0 else L, self.ref)


class Hc08(CycleModel):
    part = "74HC08"

    def eval_comb(self) -> bool:
        return self._gate(lambda a, b: a & b)

    def _gate(self, fn: Callable[[int, int], int]) -> bool:
        a, b = self.read_bit("A"), self.read_bit("B")
        if a > 1 or b > 1:
            return False
        return self.ctx.drive_net(self.net_for("Y"), fn(a, b), self.ref)


class Hc32(Hc08):
    part = "74HC32"

    def eval_comb(self) -> bool:
        return self._gate(lambda a, b: a | b)


class Hc86(Hc08):
    part = "74HC86"

    def eval_comb(self) -> bool:
        return self._gate(lambda a, b: a ^ b)


class Hc153(CycleModel):
    part = "74HC153"

    def eval_comb(self) -> bool:
        changed = False
        for ch in ("1", "2"):
            y_pin = f"{ch}Y"
            if y_pin not in self.pin_nets:
                continue
            g = self.read_bit(f"{ch}G")
            if g == 1:
                changed |= self.ctx.drive_net(self.net_for(y_pin), L, self.ref)
                continue
            a, b = self.read_bit("A"), self.read_bit("B")
            if a > 1 or b > 1:
                continue
            sel = a | (b << 1)
            if sel > 3:
                continue
            c_pin = f"{ch}C{sel}"
            if c_pin not in self.pin_nets:
                continue
            val = self.read_bit(c_pin)
            if val > 1:
                continue
            changed |= self.ctx.drive_net(self.net_for(y_pin), val, self.ref)
        return changed


class Hc153Slice(CycleModel):
    part = "ALU_153_SLICE"

    def eval_comb(self) -> bool:
        g = self.read_bit("G")
        if g == 1:
            return self.ctx.drive_net(self.net_for("Y"), L, self.ref)
        a, b = self.read_bit("A"), self.read_bit("B")
        if a > 1 or b > 1:
            return False
        sel = a | (b << 1)
        if sel > 3:
            return False
        c_pin = f"C{sel}"
        if c_pin not in self.pin_nets:
            return False
        val = self.read_bit(c_pin)
        if val > 1:
            return False
        return self.ctx.drive_net(self.net_for("Y"), val, self.ref)


class Hc157(CycleModel):
    part = "74HC157"

    def eval_comb(self) -> bool:
        changed = False
        oe = self.read_bit("OE")
        s = self.read_bit("S")
        for i in range(1, 5):
            y_pin = f"{i}Y"
            if y_pin not in self.pin_nets:
                continue
            if oe == 1:
                changed |= self.ctx.drive_net(self.net_for(y_pin), Z, self.ref)
                continue
            a_pin, b_pin = f"{i}A", f"{i}B"
            if a_pin not in self.pin_nets or b_pin not in self.pin_nets:
                continue
            a, b = self.read_bit(a_pin), self.read_bit(b_pin)
            if a > 1 or b > 1:
                continue
            y = a if s == 0 else b
            changed |= self.ctx.drive_net(self.net_for(y_pin), y, self.ref)
        return changed


class Hc283(CycleModel):
    part = "74HC283"

    def eval_comb(self) -> bool:
        if any(self.read(f"A{i}") > 1 for i in range(4)):
            return False
        if any(self.read(f"B{i}") > 1 for i in range(4)):
            return False
        a = sum(self.read_bit(f"A{i}") << i for i in range(4))
        b = sum(self.read_bit(f"B{i}") << i for i in range(4))
        c0 = self.read_bit("C0")
        total = a + b + c0
        s = total & 0xF
        cout = (total >> 4) & 1
        changed = False
        for i in range(4):
            changed |= self.ctx.drive_net(self.net_for(f"S{i}"), (s >> i) & 1, self.ref)
        changed |= self.ctx.drive_net(self.net_for("C4"), cout, self.ref)
        return changed


class AluYMuxSel(CycleModel):
    part = "ALU_Y_MUX_SEL"

    def eval_comb(self) -> bool:
        s0, s1 = self.read_bit("S0"), self.read_bit("S1")
        if s0 > 1 or s1 > 1:
            return False
        sel = H if (s0 or s1) else L
        return self.ctx.drive_net(self.net_for("SEL"), sel, self.ref)


class AluCmpFromSub(CycleModel):
    part = "ALU_CMP_SUB"

    def eval_comb(self) -> bool:
        if self.read_bit("B_SEL") != 1 or self.read_bit("CIN") != 1:
            return False
        ys = [self.read_bit(f"Y{i}") for i in range(8)]
        if any(y > 1 for y in ys):
            return False
        z = H if all(y == 0 for y in ys) else L
        c_hi = self.read_bit("C_HI")
        if c_hi > 1:
            return False
        changed = self.ctx.drive_net(self.net_for("Z"), z, self.ref)
        changed |= self.ctx.drive_net(self.net_for("C_GE"), c_hi, self.ref)
        return changed


class YBusBuf(CycleModel):
    """Tri-state Y → D bus (combinational enable)."""

    part = "Y_BUS_BUF"

    def eval_comb(self) -> bool:
        oe = self.read_bit("Y_OE")
        if oe > 1:
            return False
        changed = False
        for i in range(8):
            pin_y, pin_d = f"Y{i}", f"D{i}"
            if pin_y not in self.pin_nets or pin_d not in self.pin_nets:
                continue
            if oe == 1:
                y = self.read_bit(pin_y)
                if y > 1:
                    continue
                changed |= self.ctx.drive_net(self.net_for(pin_d), y, self.ref)
            else:
                changed |= self.ctx.drive_net(self.net_for(pin_d), Z, self.ref)
        return changed
