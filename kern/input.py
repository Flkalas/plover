"""Host-side input driver — Mailbox HID wrapper."""

from __future__ import annotations

from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.hid import CMD_HID_INJECT, CMD_HID_KEY_READ, CMD_HID_MOUSE_READ, CMD_HID_POLL, INJECT_KEY, INJECT_MOUSE
from plover_vm.memory.mailbox import MB_BUFFER, MB_CMD, MB_PARAM, MB_STATUS, ST_HID_KEY_PENDING, ST_HID_MOUSE_PENDING

SIG_HID = 0x48


class InputDriver:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus

    def _issue(self, cmd: int, param: int = 0, *, buffer: bytes | bytearray | None = None) -> None:
        self.bus.write_cpu(MB_PARAM, param)
        if buffer is not None:
            for i, b in enumerate(buffer[:248]):
                self.bus.write_cpu(MB_BUFFER + i, b)
        self.bus.write_cpu(MB_CMD, cmd)

    def poll(self) -> tuple[int, int]:
        self._issue(CMD_HID_POLL)
        mb = self.bus.mailbox
        return mb._buffer[0], mb._buffer[1]

    def read_key(self) -> int:
        self._issue(CMD_HID_KEY_READ)
        return self.bus.mailbox._buffer[0] & 0xFF

    def read_mouse(self) -> tuple[int, int, int]:
        self._issue(CMD_HID_MOUSE_READ)
        buf = self.bus.mailbox._buffer
        dx = buf[1] if buf[1] < 128 else buf[1] - 256
        dy = buf[2] if buf[2] < 128 else buf[2] - 256
        return buf[0] & 0xFF, dx, dy

    def inject_key(self, ch: int) -> None:
        self._issue(CMD_HID_INJECT, buffer=bytes([INJECT_KEY, ch & 0xFF]))

    def inject_mouse(self, buttons: int, dx: int, dy: int) -> None:
        self._issue(
            CMD_HID_INJECT,
            buffer=bytes([INJECT_MOUSE, buttons & 0x07, dx & 0xFF, dy & 0xFF]),
        )

    def key_pending(self) -> bool:
        return bool(self.bus.read_cpu(MB_STATUS) & ST_HID_KEY_PENDING)

    def mouse_pending(self) -> bool:
        return bool(self.bus.read_cpu(MB_STATUS) & ST_HID_MOUSE_PENDING)
