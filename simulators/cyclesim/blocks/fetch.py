"""Fetch path — PC, IR, MBR, addr MUX, memory array."""

from __future__ import annotations

from simulators.cyclesim.blocks.mem_decode import MAILBOX_BASE, MemSystem
from simulators.cyclesim.engine import Block, SimContext
from simulators.cyclesim.values import H, L


class PcReg(Block):
    def __init__(self, name: str = "pc") -> None:
        super().__init__(name)
        self.pc = 0

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        for i in range(16):
            changed |= ctx.drive(f"net_pc{i}", (self.pc >> i) & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if ctx.get("net_pc_load") & 1:
            val = sum((ctx.get(f"net_pc_in{i}") & 1) << i for i in range(16))
            self.pc = val & 0xFFFF
        elif ctx.get("net_pc_inc") & 1:
            self.pc = (self.pc + 1) & 0xFFFF


class IrReg(Block):
    def __init__(self, name: str = "ir") -> None:
        super().__init__(name)
        self.ir = 0

    @property
    def opcode(self) -> int:
        return self.ir & 0xFF

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_ir{i}", (self.ir >> i) & 1, self.name)
        for i in range(5):
            changed |= ctx.drive(f"net_opc{i}", ((self.ir >> i) & 1), self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if ctx.get("net_ir_load") & 1:
            self.ir = sum((ctx.get(f"net_mem_d{i}") & 1) << i for i in range(8)) & 0xFF


class MbrReg(Block):
    def __init__(self, name: str = "mbr") -> None:
        super().__init__(name)
        self.mbr = 0

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_mbr{i}", (self.mbr >> i) & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if ctx.get("net_mbr_load") & 1:
            self.mbr = sum((ctx.get(f"net_mem_d{i}") & 1) << i for i in range(8)) & 0xFF


class Abs16HiReg(Block):
    """High byte latch for BEQ/JMP/STA16 abs16 operand."""

    def __init__(self, name: str = "abs16_hi") -> None:
        super().__init__(name)
        self.hi = 0

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_abs16_hi{i}", (self.hi >> i) & 1, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if ctx.get("net_abs16_hi_load") & 1:
            self.hi = sum((ctx.get(f"net_mem_d{i}") & 1) << i for i in range(8)) & 0xFF


class PcInMux(Block):
    """Branch target: PC_in = abs16_hi:MBR."""

    def __init__(self, name: str = "pc_in_mux") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_pc_in{i}", ctx.get(f"net_mbr{i}") & 1, self.name)
        for i in range(8):
            changed |= ctx.drive(f"net_pc_in{i + 8}", ctx.get(f"net_abs16_hi{i}") & 1, self.name)
        return changed


class AddrMux(Block):
    """FETCH=1 -> PC; data mode -> MBR / LDIO / abs16 effective address."""

    def __init__(self, name: str = "addr_mux") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        fetch = ctx.get("net_fetch") & 1
        changed = False
        if fetch:
            for i in range(16):
                changed |= ctx.drive(f"net_addr{i}", ctx.get(f"net_pc{i}") & 1, self.name)
            return changed
        if ctx.get("net_ldio_stio") & 1:
            addr = MAILBOX_BASE | sum((ctx.get(f"net_mbr{i}") & 1) << i for i in range(8))
        elif ctx.get("net_abs16_addr") & 1:
            lo = sum((ctx.get(f"net_mbr{i}") & 1) << i for i in range(8))
            hi = sum((ctx.get(f"net_abs16_hi{i}") & 1) << i for i in range(8))
            addr = lo | (hi << 8)
        else:
            addr = sum((ctx.get(f"net_mbr{i}") & 1) << i for i in range(8))
        for i in range(16):
            changed |= ctx.drive(f"net_addr{i}", (addr >> i) & 1, self.name)
        return changed


class MemArray(Block):
    def __init__(self, name: str = "mem") -> None:
        super().__init__(name)
        self.sys = MemSystem()

    def load_hex(self, path: str, *, target: str = "rom") -> None:
        self.sys.load_hex(path, target=target)

    def load_bytes(self, base: int, blob: bytes, *, target: str = "rom") -> None:
        self.sys.load_bytes(base, blob, target=target)

    def load_ram(self, addr: int, val: int) -> None:
        self.sys.load_ram(addr, val)

    def set_vector(self, pc: int) -> None:
        self.sys.set_vector(pc)

    @property
    def map_mode(self) -> int:
        return self.sys.map_mode

    @map_mode.setter
    def map_mode(self, val: int) -> None:
        self.sys.map_mode = val & 1

    def read(self, addr: int) -> int:
        return self.sys.read(addr)

    def write(self, addr: int, val: int) -> None:
        self.sys.write(addr, val)

    def eval_comb(self, ctx: SimContext) -> bool:
        addr = sum((ctx.get(f"net_addr{i}") & 1) << i for i in range(16))
        reading = (ctx.get("net_mem_rd") & 1) or (ctx.get("net_fetch") & 1)
        byte = self.sys.read(addr) if reading else 0
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_mem_d{i}", (byte >> i) & 1, self.name)
        return changed


class FlgReg(Block):
    def __init__(self, name: str = "flg") -> None:
        super().__init__(name)
        self.z = False
        self.c = False

    def eval_comb(self, ctx: SimContext) -> bool:
        changed = False
        changed |= ctx.drive("net_flg_z", H if self.z else L, self.name)
        changed |= ctx.drive("net_flg_c", H if self.c else L, self.name)
        return changed

    def tick(self, ctx: SimContext) -> None:
        if ctx.get("net_flg_we") & 1:
            self.z = (ctx.get("net_cmp_z") & 1) == H
            self.c = (ctx.get("net_c_hi") & 1) == H


class YBusMux(Block):
    """MEM_ST ph0: Y_OE drives q_a (R0) onto D bus; else ALU Y when y_oe."""

    def __init__(self, name: str = "y_bus_mux") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        if not (ctx.get("net_y_oe") & 1):
            return False
        changed = False
        if ctx.get("net_y_src_a") & 1:
            for i in range(8):
                changed |= ctx.drive(f"net_d{i}", ctx.get(f"net_a{i}") & 1, self.name)
        return changed
