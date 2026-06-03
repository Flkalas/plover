"""Ideal CPLD_SYSTEM_CTRL — zero-delay comb decode."""

from __future__ import annotations

from cyclesim.models.base import CycleModel
from hw.logic import cpld_decode


class CpldSystemCtrl(CycleModel):
    part = "CPLD_SYSTEM_CTRL"

    def eval_comb(self) -> bool:
        addr = sum(self.read_bit(f"A{i}") << i for i in range(16) if f"A{i}" in self.pin_nets)
        op = sum(self.read_bit(f"OPC{i}") << i for i in range(4) if f"OPC{i}" in self.pin_nets)
        ph = sum(self.read_bit(f"PH{i}") << i for i in range(2) if f"PH{i}" in self.pin_nets)
        rst = self.read_bit("RESET_N") == 0
        map_mode = self.read_bit("MAP_MODE")
        reg_we = self.read_bit("REG_WE") if "REG_WE" in self.pin_nets else 0

        mem = cpld_decode.decode_addr(addr, map_mode, rst)
        gpr = cpld_decode.decode_gpr(op & 0xF, ph & 3, reg_we)

        changed = False
        changed |= self.ctx.drive_net(self.net_for("MAILBOX_EN"), mem.mailbox_en, self.ref)
        changed |= self.ctx.drive_net(self.net_for("RAM1_CS_N"), mem.ram1_cs_n, self.ref)
        changed |= self.ctx.drive_net(self.net_for("RAM2_CS_N"), mem.ram2_cs_n, self.ref)
        changed |= self.ctx.drive_net(self.net_for("ROM_CS_N"), mem.rom_cs_n, self.ref)
        changed |= self.ctx.drive_net(self.net_for("ADDR_FORCE_FFFC"), mem.addr_force_fffc, self.ref)
        if "REG_SEL0" in self.pin_nets:
            changed |= self.ctx.drive_net(self.net_for("REG_SEL0"), gpr.reg_sel0, self.ref)
            changed |= self.ctx.drive_net(self.net_for("REG_SEL1"), gpr.reg_sel1, self.ref)
        for r in range(4):
            pin = f"LOAD_R{r}"
            if pin in self.pin_nets:
                changed |= self.ctx.drive_net(self.net_for(pin), gpr.load_r[r], self.ref)
        return changed
