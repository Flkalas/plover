"""Combinational 74HC and ALU glue models (logic from hw.logic.gates)."""

from __future__ import annotations

from typing import Callable

from cyclesim.models.base import CycleModel, H, L, X, Z
from hw.logic import gates


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
        val = gates.eval_alu_153_slice(self.read_bit)
        if val is None:
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
        result = gates.eval_hc283(self.read_bit, self.read)
        if result is None:
            return False
        s, cout = result
        changed = False
        for i in range(4):
            changed |= self.ctx.drive_net(self.net_for(f"S{i}"), (s >> i) & 1, self.ref)
        changed |= self.ctx.drive_net(self.net_for("C4"), cout, self.ref)
        return changed


class AluIncBSel(CycleModel):
    part = "ALU_INC_B_SEL"

    def eval_comb(self) -> bool:
        drives = gates.eval_alu_inc_b_sel(
            self.read_bit,
            lambda p: p in self.pin_nets,
        )
        if drives is None:
            return False
        changed = False
        for pin_d, val in drives.items():
            changed |= self.ctx.drive_net(self.net_for(pin_d), val, self.ref)
        return changed


class AluInc2c2(CycleModel):
    part = "ALU_INC_2C2"

    def eval_comb(self) -> bool:
        drives = gates.eval_alu_inc_2c2(
            self.read_bit,
            lambda p: p in self.pin_nets,
        )
        if drives is None:
            return False
        changed = False
        for pin_d, val in drives.items():
            changed |= self.ctx.drive_net(self.net_for(pin_d), val, self.ref)
        return changed


class AluYMuxSel(CycleModel):
    part = "ALU_Y_MUX_SEL"

    def eval_comb(self) -> bool:
        sel = gates.eval_alu_y_mux_sel(self.read_bit)
        if sel is None:
            return False
        return self.ctx.drive_net(self.net_for("SEL"), sel, self.ref)


class AluCmpFromSub(CycleModel):
    part = "ALU_CMP_SUB"

    def eval_comb(self) -> bool:
        result = gates.eval_alu_cmp_from_sub(self.read_bit)
        if result is None:
            return False
        z, c_hi = result
        changed = self.ctx.drive_net(self.net_for("Z"), z, self.ref)
        changed |= self.ctx.drive_net(self.net_for("C_GE"), c_hi, self.ref)
        return changed


class YBusBuf(CycleModel):
    """Tri-state Y → D bus (combinational enable)."""

    part = "Y_BUS_BUF"

    def eval_comb(self) -> bool:
        drives = gates.eval_y_bus_buf(
            self.read_bit,
            lambda p: p in self.pin_nets,
        )
        if drives is None:
            return False
        changed = False
        for pin_d, val in drives.items():
            changed |= self.ctx.drive_net(self.net_for(pin_d), val, self.ref)
        return changed
