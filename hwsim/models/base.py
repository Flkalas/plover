"""Chip behavioral models for event-driven simulation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hw.logic import cpld_decode, gates
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
        if net in (self.net_for("A"),):
            self._update()

    def _update(self) -> None:
        a = self.read_bit("A")
        if a > 1:
            return
        y = 1 - a
        t = self.t_pd("74HC04", "t_pd", default=9)
        self._drive("Y", y, t, "inv")


class Hc151(ChipModel):
    """74HC151 8-to-1 data selector; W active-low enable."""

    part = "74HC151"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        t = self.t_pd("74HC151", "t_pd", default=17)
        w = self.read_bit("W")
        if w == 1:
            self._drive("Y", 0, t, "disabled")
            return
        sel = self.read_bit("S0") | (self.read_bit("S1") << 1) | (self.read_bit("S2") << 2)
        val = self.read_bit(f"D{sel}")
        if val > 1:
            return
        self._drive("Y", val, t, "mux")


class Hc153(ChipModel):
    """74HC153 dual 4-to-1 multiplexer; 1G/2G active-low enable."""

    part = "74HC153"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        t = self.t_pd("74HC153", "t_pd", default=17)
        for ch in ("1", "2"):
            y_pin = f"{ch}Y"
            if y_pin not in self.pin_nets:
                continue
            g = self.read_bit(f"{ch}G")
            if g == 1:
                self._drive(y_pin, 0, t, "disabled")
                continue
            sel = self.read_bit("A") | (self.read_bit("B") << 1)
            val = self.read_bit(f"{ch}C{sel}")
            if val > 1:
                continue
            self._drive(y_pin, val, t, "mux")


class Hc157(ChipModel):
    """74HC157 quad 2-to-1 multiplexer; OE active-low."""

    part = "74HC157"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        oe = self.read_bit("OE")
        t = self.t_pd("74HC157", "t_pd", default=11)
        s = self.read_bit("S")
        for i in range(1, 5):
            y_pin = f"{i}Y"
            if y_pin not in self.pin_nets:
                continue
            if oe == 1:
                self._drive(y_pin, 3, t, "z")
                continue
            a_pin, b_pin = f"{i}A", f"{i}B"
            if a_pin not in self.pin_nets or b_pin not in self.pin_nets:
                continue
            a = self.read_bit(a_pin)
            b = self.read_bit(b_pin)
            if a > 1 or b > 1:
                continue
            y = a if s == 0 else b
            self._drive(y_pin, y, t, "mux")


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
        result = gates.eval_hc283(self.read_bit, self.read)
        if result is None:
            return
        s, cout = result
        t_sum = self.t_pd("74HC283", "t_pd", "sum", default=30)
        t_cout = self.t_pd("74HC283", "t_pd", "cout", default=30)
        for i in range(4):
            self._drive(f"S{i}", (s >> i) & 1, t_sum, "sum")
        self._drive("C4", cout, t_cout, "cout")


class Hc574(ChipModel):
    part = "74HC574"

    def _cp_pin(self) -> str:
        if "CP" in self.pin_nets:
            return "CP"
        if "CLK" in self.pin_nets:
            return "CLK"
        return "CP"

    def on_start(self) -> None:
        self._prev_clk[self._cp_pin()] = self.read_bit(self._cp_pin())
        oe = self.read_bit("OE")
        if oe == 1:
            for i in range(8):
                self._drive(f"Q{i}", 3, 0, "high-z")  # Z

    def on_net_change(self, net: str) -> None:
        cp = self._cp_pin()
        cp_net = self.net_for(cp)
        if net == cp_net or any(net == self.net_for(f"D{i}") for i in range(8)):
            if self._posedge(cp):
                self._latch()
        if net == self.net_for("OE"):
            self._output_enable()

    def _latch(self) -> None:
        cp = self._cp_pin()
        t = self.t_pd("74HC574", "t_pd_q", default=15)
        t_su = self.t_pd("74HC574", "t_setup", default=5)
        ok = True
        for i in range(8):
            if not self.ctx.check_setup(self.ref, cp, f"D{i}", t_su):
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
        self._q = 0
        cp = "CP"
        self._prev_clk[cp] = self.read_bit(cp)
        self._drive_q(0, "init")
        self._drive_tc(0, 0)

    def on_net_change(self, net: str) -> None:
        if "MR" in self.pin_nets and self.read_bit("MR") == 0:
            self._q = 0
            self._drive_q(self.t_pd("74HC161", "t_clk_to_q", default=15), "async reset")
            self._drive_tc(0, 15)
            return
        cp_net = self.net_for("CP")
        if net == cp_net and self._posedge("CP"):
            t = self.t_pd("74HC161", "t_clk_to_q", default=15)
            pe = self.read_bit("PE") if "PE" in self.pin_nets else 0
            if pe:
                self._q = sum(self.read_bit(f"P{i}") << i for i in range(4))
                self._drive_q(t, "load")
            elif self.read_bit("CEP") and self.read_bit("CET"):
                self._q = (self._q + 1) & 0xF
                self._drive_q(t, "count")
            self._drive_tc(1 if self._q == 0xF else 0, t)
            return
        if net in {self.net_for(f"Q{i}") for i in range(4)}:
            self._drive_tc(1 if self._q == 0xF else 0, 0)

    def _drive_q(self, delay: int, reason: str) -> None:
        for i in range(4):
            self._drive(f"Q{i}", (self._q >> i) & 1, delay, reason)

    def _drive_tc(self, value: int, delay: int) -> None:
        if "TC" in self.pin_nets:
            self._drive("TC", value, delay, "tc")


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


class AluCmpFromSub(ChipModel):
    """CMP flags from SUB datapath: Z = (Y==0), C_GE = net_c_hi (no 74HC85 on breadboard)."""

    part = "ALU_CMP_SUB"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        result = gates.eval_alu_cmp_from_sub(self.read_bit)
        if result is None:
            return
        z, c_hi = result
        t = self.t_pd("ALU_CMP_SUB", "t_pd", default=151)
        self._drive("Z", z, t, "cmp_sub")
        self._drive("C_GE", c_hi, t, "cmp_sub")


class Hc153Slice(ChipModel):
    """Single 74HC153 4:1 mux (Gigatron ALU bit-slice); A/B are operand select lines."""

    part = "ALU_153_SLICE"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        val = gates.eval_alu_153_slice(self.read_bit)
        if val is None:
            return
        t = self.t_pd("ALU_153_SLICE", "t_pd", default=17)
        self._drive("Y", val, t, "mux")


class YBusBuf(ChipModel):
    """CW Y_OE → tri-state ALU Y onto data bus (74HC245-style per bit)."""

    part = "Y_BUS_BUF"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        if net == self.net_for("Y_OE"):
            self._update()
            return
        for i in range(8):
            pin = f"Y{i}"
            if pin in self.pin_nets and net == self.net_for(pin):
                self._update()
                return

    def _update(self) -> None:
        t = self.t_pd("Y_BUS_BUF", "t_pd", default=11)
        drives = gates.eval_y_bus_buf(
            self.read_bit,
            lambda p: p in self.pin_nets,
        )
        if drives is None:
            return
        for pin_d, val in drives.items():
            self._drive(pin_d, val, t, "y_bus" if val != gates.Z else "high-z")


class AluYMuxSel(ChipModel):
    """157 Y bypass select: SEL = S0|S1 (logic → B=net_y_logic, arith → A=net_sum)."""

    part = "ALU_Y_MUX_SEL"

    def on_start(self) -> None:
        self._update()

    def on_net_change(self, net: str) -> None:
        self._update()

    def _update(self) -> None:
        sel = gates.eval_alu_y_mux_sel(self.read_bit)
        if sel is None:
            return
        t = self.t_pd("ALU_Y_MUX_SEL", "t_pd", default=5)
        self._drive("SEL", sel, t, "y_mux_sel")


class Hc08(ChipModel):
    part = "74HC08"

    def on_start(self) -> None:
        self._gate(lambda a, b: a & b)

    def on_net_change(self, net: str) -> None:
        if net in (self.net_for("A"), self.net_for("B")):
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
        if net in (self.net_for("A"), self.net_for("B")):
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
        if net in (self.net_for("A"), self.net_for("B")):
            self._gate(lambda a, b: a ^ b)

    def _gate(self, fn: Any) -> None:
        a = self.read_bit("A")
        b = self.read_bit("B")
        if a > 1 or b > 1:
            return
        t = self.t_pd("74HC86", "t_pd", default=9)
        self._drive("Y", fn(a, b), t, "xor")


class CpldSystemCtrl(ChipModel):
    """Ideal comb ATF1504AS decode — zero internal state; t_pd=0 in hwsim (VM owns phase/clock)."""

    part = "CPLD_SYSTEM_CTRL"

    def on_start(self) -> None:
        self._update(0)

    def on_net_change(self, net: str) -> None:
        self._update(0)

    def _addr(self) -> int:
        v = 0
        for i in range(16):
            if f"A{i}" in self.pin_nets:
                v |= self.read_bit(f"A{i}") << i
        return v

    def _opcode_phase(self) -> tuple[int, int]:
        op = sum(self.read_bit(f"OPC{i}") << i for i in range(4) if f"OPC{i}" in self.pin_nets)
        ph = sum(self.read_bit(f"PH{i}") << i for i in range(2) if f"PH{i}" in self.pin_nets)
        return op & 0xF, ph & 3

    def _update(self, delay: int) -> None:
        t = delay if delay else self.t_pd("CPLD_SYSTEM_CTRL", "t_pd", default=0)
        a = self._addr()
        rst = self.read_bit("RESET_N") == 0
        map_mode = self.read_bit("MAP_MODE")
        mem = cpld_decode.decode_addr(a, map_mode, rst)
        self._drive("MAILBOX_EN", mem.mailbox_en, t, "mailbox")
        self._drive("RAM1_CS_N", mem.ram1_cs_n, t, "ram1")
        self._drive("RAM2_CS_N", mem.ram2_cs_n, t, "ram2")
        self._drive("ROM_CS_N", mem.rom_cs_n, t, "rom")
        self._drive("ADDR_FORCE_FFFC", mem.addr_force_fffc, t, "reset_vec")

        op, ph = self._opcode_phase()
        reg_we = self.read_bit("REG_WE") if "REG_WE" in self.pin_nets else 0
        gpr = cpld_decode.decode_gpr(op, ph, reg_we)
        for r in range(4):
            pin = f"LOAD_R{r}"
            if pin in self.pin_nets:
                self._drive(pin, gpr.load_r[r], t, f"load_r{r}")
        if "REG_SEL0" in self.pin_nets:
            self._drive("REG_SEL0", gpr.reg_sel0, t, "sel")
            self._drive("REG_SEL1", gpr.reg_sel1, t, "sel")


class MemDecodeBreadboard(ChipModel):
    """v1.0 breadboard — 138×2 + gate ideal comb (truth via decode_ce_breadboard)."""

    part = "MEM_DECODE_BREADBOARD"

    def on_start(self) -> None:
        self._update(0)

    def on_net_change(self, net: str) -> None:
        self._update(0)

    def _addr(self) -> int:
        v = 0
        for i in range(16):
            if f"A{i}" in self.pin_nets:
                v |= self.read_bit(f"A{i}") << i
        return v

    def _update(self, delay: int) -> None:
        t = delay if delay else self.t_pd("CPLD_SYSTEM_CTRL", "t_pd", default=0)
        a = self._addr()
        rst = self.read_bit("RESET_N") == 0
        map_mode = self.read_bit("MAP_MODE")
        mem = cpld_decode.decode_ce_breadboard(a, map_mode, rst)
        self._drive("MAILBOX_EN", mem.mailbox_en, t, "mailbox")
        self._drive("RAM1_CS_N", mem.ram1_cs_n, t, "ram1")
        self._drive("RAM2_CS_N", mem.ram2_cs_n, t, "ram2")
        self._drive("ROM_CS_N", mem.rom_cs_n, t, "rom")
        self._drive("ADDR_FORCE_FFFC", mem.addr_force_fffc, t, "reset_vec")


class CpldGprCtrl(ChipModel):
    """v1.0 ATF1504 GPR routing — REG_SEL from latched CW."""

    part = "CPLD_GPR_CTRL"

    def on_start(self) -> None:
        self._update(0)

    def on_net_change(self, net: str) -> None:
        self._update(0)

    def _update(self, delay: int) -> None:
        t = delay if delay else self.t_pd("CPLD_SYSTEM_CTRL", "t_pd", default=0)
        reg_sel = self.read_bit("REG_SEL0") | (self.read_bit("REG_SEL1") << 1)
        reg_we = self.read_bit("REG_WE") if "REG_WE" in self.pin_nets else 0
        gpr = cpld_decode.decode_gpr_from_cw(reg_sel, reg_we)
        if "W_SEL0" in self.pin_nets:
            self._drive("W_SEL0", gpr.w_sel & 1, t, "wsel")
            self._drive("W_SEL1", (gpr.w_sel >> 1) & 1, t, "wsel")
        if "R_SEL_A0" in self.pin_nets:
            self._drive("R_SEL_A0", gpr.r_sel_a & 1, t, "rsel_a")
            self._drive("R_SEL_A1", (gpr.r_sel_a >> 1) & 1, t, "rsel_a")
        if "R_SEL_B0" in self.pin_nets:
            self._drive("R_SEL_B0", gpr.r_sel_b & 1, t, "rsel_b")
            self._drive("R_SEL_B1", (gpr.r_sel_b >> 1) & 1, t, "rsel_b")


class CpldSystemCtrlTier2(MemDecodeBreadboard):
    """Deprecated alias — use MEM_DECODE_BREADBOARD."""

    part = "CPLD_SYSTEM_CTRL_TIER2"


class CpldRegfile(ChipModel):
    """4×8-bit GPR inside ATF1504 — async dual read, sync write on WE∧CLK↑."""

    part = "CPLD_REGFILE"

    def on_start(self) -> None:
        self._regs = [0, 0, 0, 0]
        self._prev_clk["CLK"] = self.read_bit("CLK")
        self._read_out(0)

    def on_net_change(self, net: str) -> None:
        watched = {self.net_for("CLK"), self.net_for("WE")}
        for p in ("W_SEL0", "W_SEL1", "R_SEL_A0", "R_SEL_A1", "R_SEL_B0", "R_SEL_B1"):
            if p in self.pin_nets:
                watched.add(self.net_for(p))
        for i in range(8):
            watched.add(self.net_for(f"D{i}"))
        if net not in watched:
            return
        if self._posedge("CLK") and self.read_bit("WE") == 1:
            self._write()
        self._read_out(0)

    def _write(self) -> None:
        t_su = self.t_pd("CPLD_REGFILE", "t_setup", default=5)
        for i in range(8):
            if not self.ctx.check_setup(self.ref, "CLK", f"D{i}", t_su):
                return
        w_sel = self.read_bit("W_SEL0") | (self.read_bit("W_SEL1") << 1)
        d = sum(self.read_bit(f"D{i}") << i for i in range(8))
        self._regs[w_sel & 3] = d & 0xFF

    def _read_out(self, delay: int) -> None:
        t = delay or self.t_pd("CPLD_REGFILE", "t_pd", default=10)
        ra = self.read_bit("R_SEL_A0") | (self.read_bit("R_SEL_A1") << 1)
        rb = self.read_bit("R_SEL_B0") | (self.read_bit("R_SEL_B1") << 1)
        qa = self._regs[ra & 3]
        qb = self._regs[rb & 3]
        for i in range(8):
            self._drive(f"QA{i}", (qa >> i) & 1, t, "qa")
            self._drive(f"QB{i}", (qb >> i) & 1, t, "qb")


class Regfile574Gpr(ChipModel):
    """4×8-bit GPR via 574 behavior — LOAD_R* + CLK, dual read ports."""

    part = "REGFILE_574_GPR"

    def on_start(self) -> None:
        self._regs = [0, 0, 0, 0]
        self._prev_clk["CLK"] = self.read_bit("CLK")
        self._read_out(0)

    def on_net_change(self, net: str) -> None:
        watched = {self.net_for("CLK"), self.net_for("REG_WE")}
        for r in range(4):
            if f"LOAD_R{r}" in self.pin_nets:
                watched.add(self.net_for(f"LOAD_R{r}"))
        for i in range(8):
            watched.add(self.net_for(f"D{i}"))
        for p in ("RA0", "RA1", "RB0", "RB1"):
            if p in self.pin_nets:
                watched.add(self.net_for(p))
        if net not in watched:
            return
        if self._posedge("CLK"):
            self._maybe_write()
        self._read_out(0)

    def _maybe_write(self) -> None:
        if self.read_bit("REG_WE") == 0:
            return
        t_su = self.t_pd("74HC574", "t_setup", default=5)
        for i in range(8):
            if not self.ctx.check_setup(self.ref, "CLK", f"D{i}", t_su):
                return
        updated = gates.regfile_maybe_write(
            self._regs,
            self.read_bit,
            lambda p: p in self.pin_nets,
        )
        if updated is not None:
            self._regs = updated

    def _read_out(self, delay: int) -> None:
        t = delay or self.t_pd("74HC574", "t_pd_q", default=15)
        qa, qb = gates.regfile_read_ports(self._regs, self.read_bit)
        for i in range(8):
            self._drive(f"QA{i}", (qa >> i) & 1, t, "qa")
            self._drive(f"QB{i}", (qb >> i) & 1, t, "qb")


class MailboxMmio(ChipModel):
    """Behavioral MMIO mailbox @ $FF00 — STATUS/CMD/PARAM/BUFFER stub."""

    part = "MAILBOX_MMIO"

    def on_start(self) -> None:
        self._status = 0
        self._cmd = 0
        self._param = 0
        self._buf = [0] * 248
        self._update(0)

    def on_net_change(self, net: str) -> None:
        watched = {self.net_for("CS"), self.net_for("RD"), self.net_for("WE")}
        for i in range(8):
            watched.add(self.net_for(f"A{i}"))
        if net not in watched:
            return
        if self.read_bit("CS") == 1:
            self._access(0)

    def _offset(self) -> int:
        return sum(self.read_bit(f"A{i}") << i for i in range(8) if f"A{i}" in self.pin_nets)

    def _access(self, delay: int) -> None:
        off = self._offset()
        if self.read_bit("RD") and off == 0x00:
            self._update(delay)
        if self.read_bit("WE") and off == 0x01:
            self._status = 0x02  # Busy
            self._status &= ~0x01
            self._update(delay)
            self._status = 0x01  # DataReady (RP2350 done)
            self._update(self.t_pd("MAILBOX_MMIO", "t_pd", default=8))

    def _update(self, delay: int) -> None:
        t = delay or self.t_pd("MAILBOX_MMIO", "t_pd", default=8)
        for i in range(8):
            if f"STATUS{i}" in self.pin_nets:
                self._drive(f"STATUS{i}", (self._status >> i) & 1, t, "st")


class RomCtrlFlash(ChipModel):
    """SST39 / control-store Flash — addr → D after ROM_CTRL.t_pd (70 ns max)."""

    part = "ROM_CTRL"
    _words_cache: dict[int, int] | None = None

    @classmethod
    def _rom_words(cls) -> dict[int, int]:
        if cls._words_cache is not None:
            return cls._words_cache
        path = Path(__file__).resolve().parents[2] / "hw" / "fixtures" / "control" / "cw.hex"
        words: dict[int, int] = {}
        if path.is_file():
            raw = [
                int(line.strip(), 16)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            for idx in range(len(raw) // 2):
                words[idx] = raw[2 * idx] | (raw[2 * idx + 1] << 8)
        cls._words_cache = words
        return words

    def on_start(self) -> None:
        self._update(0)

    def on_net_change(self, net: str) -> None:
        watched = {self.net_for("OE")}
        for i in range(16):
            pin = f"A{i}"
            if pin in self.pin_nets:
                watched.add(self.net_for(pin))
        if net in watched:
            self._update(self.t_pd("ROM_CTRL", "t_pd", default=70))

    def _addr(self) -> int:
        v = 0
        for i in range(16):
            pin = f"A{i}"
            if pin in self.pin_nets:
                v |= self.read_bit(pin) << i
        return v

    def _update(self, delay: int) -> None:
        oe = self.read_bit("OE")
        if oe == 1:
            t = delay if delay else self.t_pd("ROM_CTRL", "t_pd", default=70)
            for i in range(16):
                pin = f"D{i}"
                if pin in self.pin_nets:
                    self._drive(pin, 3, t, "rom-z")
            return
        addr = self._addr()
        word = self._rom_words().get(addr, 0)
        lo = word & 0xFF
        hi = (word >> 8) & 0xFF
        t = delay if delay else self.t_pd("ROM_CTRL", "t_pd", default=70)
        for b in range(8):
            pin_lo = f"D{b}"
            if pin_lo in self.pin_nets:
                self._drive(pin_lo, (lo >> b) & 1, t, "rom")
            pin_hi = f"D{b + 8}"
            if pin_hi in self.pin_nets:
                self._drive(pin_hi, (hi >> b) & 1, t, "rom")


class FlashCw16(RomCtrlFlash):
    part = "FLASH_CW16"


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
        "74HC151": Hc151,
        "74HC153": Hc153,
        "ALU_153_SLICE": Hc153Slice,
        "74HC157": Hc157,
        "ALU_CMP_SUB": AluCmpFromSub,
        "Y_BUS_BUF": YBusBuf,
        "ALU_Y_MUX_SEL": AluYMuxSel,
        "74HC08": Hc08,
        "74HC32": Hc32,
        "74HC86": Hc86,
        "ROM_CTRL": RomCtrlFlash,
        "FLASH_CW16": FlashCw16,
        "SST39SF010A": RomCtrlFlash,
        "CPLD_SYSTEM_CTRL": CpldSystemCtrl,
        "MEM_DECODE_BREADBOARD": MemDecodeBreadboard,
        "CPLD_GPR_CTRL": CpldGprCtrl,
        "CPLD_SYSTEM_CTRL_TIER2": CpldSystemCtrlTier2,
        "ATF1504AS": CpldGprCtrl,
        "CPLD_REGFILE": CpldRegfile,
        "REGFILE_574_GPR": Regfile574Gpr,
        "MAILBOX_MMIO": MailboxMmio,
    }
    cls = table.get(part)
    if cls is None:
        raise ValueError(f"No model for part {part} ({ref})")
    return cls(ref, pins, ctx)
