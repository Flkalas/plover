"""Host-side microkernel model used for S6 bring-up.

This provides a stable syscall surface and boot flow for later VM program ports.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kern.gpio import GpioController
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import MB_BUFFER


@dataclass
class KernelState:
    heap_base: int = 0x6100
    heap_ptr: int = 0x6100
    output: list[str] = field(default_factory=list)


class Kernel:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus
        self.state = KernelState()
        self.gpio = GpioController()

    def kprint(self, s: str) -> None:
        # Simulated console: append to log and mirror into mailbox buffer for visibility.
        self.state.output.append(s)
        for i, ch in enumerate(s.encode("ascii", errors="replace")[:248]):
            self.bus.write_cpu(MB_BUFFER + i, ch)

    def kmalloc(self, n: int) -> int:
        if n <= 0:
            return self.state.heap_ptr
        p = self.state.heap_ptr
        self.state.heap_ptr = (self.state.heap_ptr + n) & 0xFFFF
        return p

    def boot(self) -> None:
        self.kprint("kernel_boot")
        self.kprint("kernel_help")
