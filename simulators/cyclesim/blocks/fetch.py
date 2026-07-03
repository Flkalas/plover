"""Fetch path — PC, IR, MBR, addr MUX, memory array."""

from __future__ import annotations

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


class AddrMux(Block):
    """FETCH=1 -> PC; FETCH=0 -> MBR (low byte) as address."""

    def __init__(self, name: str = "addr_mux") -> None:
        super().__init__(name)

    def eval_comb(self, ctx: SimContext) -> bool:
        fetch = ctx.get("net_fetch") & 1
        changed = False
        for i in range(16):
            if fetch:
                bit = (ctx.get(f"net_pc{i}") & 1)
            else:
                bit = (ctx.get(f"net_mbr{i}") & 1) if i < 8 else L
            changed |= ctx.drive(f"net_addr{i}", bit, self.name)
        return changed


class MemArray(Block):
    def __init__(self, name: str = "mem") -> None:
        super().__init__(name)
        self.data: dict[int, int] = {}

    def load_hex(self, path: str) -> None:
        addr = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for tok in line.split():
                    self.data[addr] = int(tok, 16) & 0xFF
                    addr += 1

    def load_bytes(self, base: int, blob: bytes) -> None:
        for i, b in enumerate(blob):
            self.data[base + i] = b

    def read(self, addr: int) -> int:
        return self.data.get(addr & 0xFFFF, 0)

    def write(self, addr: int, val: int) -> None:
        self.data[addr & 0xFFFF] = val & 0xFF

    def eval_comb(self, ctx: SimContext) -> bool:
        addr = sum((ctx.get(f"net_addr{i}") & 1) << i for i in range(16))
        if ctx.get("net_mem_wr") & 1:
            val = sum((ctx.get(f"net_d{i}") & 1) << i for i in range(8))
            self.write(addr, val)
        byte = self.read(addr) if (ctx.get("net_mem_rd") & 1) or (ctx.get("net_fetch") & 1) else 0
        changed = False
        for i in range(8):
            changed |= ctx.drive(f"net_mem_d{i}", (byte >> i) & 1, self.name)
        return changed
