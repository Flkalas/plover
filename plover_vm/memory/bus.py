"""Unified CPU memory bus."""

from __future__ import annotations

from plover_vm.decode import MapDecoder
from plover_vm.memory.mailbox import Mailbox
from plover_vm.memory.nor import NorFlash
from plover_vm.memory.ram import Ram64K


class MemoryBus:
    def __init__(
        self,
        nor: NorFlash | None = None,
        ram: Ram64K | None = None,
        mailbox: Mailbox | None = None,
    ) -> None:
        self.nor = nor or NorFlash()
        self.ram = ram or Ram64K()
        self.mailbox = mailbox or Mailbox()
        self.decoder = MapDecoder()
        self.map_mode = 0
        self.reset_active = False

    def fetch_addr(self, pc: int) -> int:
        if self.reset_active:
            return 0xFFFC
        return pc & 0xFFFF

    def read_cpu(self, addr: int) -> int:
        a = addr & 0xFFFF
        d = self.decoder.decode(a, self.map_mode, self.reset_active)
        if d.mailbox:
            return self.mailbox.read(a)
        if d.rom_cpu:
            return self.nor.cpu_map_read(a)
        if d.ram1 or d.ram2:
            return self.ram.read(a)
        return 0xFF

    def write_cpu(self, addr: int, val: int) -> None:
        a = addr & 0xFFFF
        d = self.decoder.decode(a, self.map_mode, self.reset_active)
        if d.mailbox:
            self.mailbox.write(a, val)
            return
        if d.rom_cpu:
            return
        if d.ram1 or d.ram2:
            self.ram.write(a, val)
