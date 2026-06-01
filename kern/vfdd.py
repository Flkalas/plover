"""Kernel-side vFDD block API (host model for S7a)."""

from __future__ import annotations

from plover_vm.memory.vfdd import VirtualFdd


class VfddDriver:
    def __init__(self, dev: VirtualFdd) -> None:
        self.dev = dev

    def read_sector(self, n: int) -> bytes:
        return self.dev.read_sector(n)

    def write_sector(self, n: int, data: bytes) -> None:
        self.dev.write_sector(n, data)

