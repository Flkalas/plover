"""Host-side microkernel model used for S6 bring-up.

This provides a stable syscall surface and boot flow for later VM program ports.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kern.audio import SIG_AUDIO, AudioDriver
from kern.gpio import GpioController
from kern.input import SIG_HID, InputDriver
from kern.serial import SIG_UART, SerialModule
from kern.video import SIG_VIDEO, VideoDriver
from plover_vm.memory.bus import MemoryBus

SIG_FDD = 0xA1
SIG_GPIO = 0xC3

DRIVER_BY_SIG = {
    SIG_FDD: "vfdd",
    SIG_HID: "hid",
    SIG_AUDIO: "audio",
    SIG_VIDEO: "video",
    SIG_GPIO: "gpio",
    SIG_UART: "serial",
}


@dataclass
class KernelState:
    heap_base: int = 0x6100
    heap_ptr: int = 0x6100
    output: list[str] = field(default_factory=list)
    slot_signatures: dict[int, int] = field(default_factory=dict)
    device_table: dict[int, str] = field(default_factory=dict)


class Kernel:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus
        self.state = KernelState()
        self.gpio = GpioController()
        self.serial = SerialModule()
        self.video = VideoDriver(bus)
        self.audio = AudioDriver(bus)
        self.input = InputDriver(bus)

    def kprint(self, s: str) -> None:
        self.state.output.append(s)
        self.serial.write((s + "\n").encode("ascii", errors="replace"))
        self.video.print(s)

    def kmalloc(self, n: int) -> int:
        if n <= 0:
            return self.state.heap_ptr
        p = self.state.heap_ptr
        self.state.heap_ptr = (self.state.heap_ptr + n) & 0xFFFF
        return p

    def devmgr_scan(self, slots: int = 16) -> dict[int, str]:
        self.state.device_table = {}
        for idx in range(slots):
            sig = self.state.slot_signatures.get(idx, 0xFF) & 0xFF
            if sig in (0x00, 0xFF):
                continue
            drv = DRIVER_BY_SIG.get(sig, "unknown")
            self.state.device_table[idx] = drv
            self.kprint(f"DEV slot{idx} sig={sig:02X} drv={drv}")
        return dict(self.state.device_table)

    def boot(self) -> None:
        if not self.state.slot_signatures:
            # default teaching/demo topology: vfdd, gpio, serial
            self.state.slot_signatures = {
                0: SIG_FDD,
                1: SIG_GPIO,
                2: SIG_UART,
                3: SIG_VIDEO,
                4: SIG_AUDIO,
                5: SIG_HID,
            }
        self.kprint("kernel_boot")
        self.devmgr_scan()
        self.kprint("kernel_help")
