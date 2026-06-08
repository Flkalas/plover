"""Host-side video driver — Mailbox VDU/GFX wrapper."""

from __future__ import annotations

from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import MB_AUX, MB_BUFFER, MB_CMD, MB_PARAM, MB_STATUS, ST_READY
from plover_vm.memory.vdu import (
    CMD_GFX_BLIT,
    CMD_GFX_FILLRECT,
    CMD_GFX_PLOT,
    CMD_VDU_ATTR,
    CMD_VDU_CLS,
    CMD_VDU_GOTO,
    CMD_VDU_PRINT,
    CMD_VDU_PUTCH,
    CMD_VDU_VSYNC,
    MODE_BOTH,
)

SIG_VIDEO = 0xB2


class VideoDriver:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus

    def _issue(self, cmd: int, param: int = 0, *, aux: int = 0, buffer: bytes | bytearray | None = None) -> None:
        self.bus.write_cpu(MB_PARAM, param)
        self.bus.write_cpu(MB_AUX, aux)
        if buffer is not None:
            for i, b in enumerate(buffer[:248]):
                self.bus.write_cpu(MB_BUFFER + i, b)
        self.bus.write_cpu(MB_CMD, cmd)

    def cls(self, attr: int = 0x07) -> None:
        self._issue(CMD_VDU_CLS, attr)

    def putch(self, ch: int) -> None:
        self._issue(CMD_VDU_PUTCH, ch & 0xFF)

    def goto(self, col: int, row: int) -> None:
        self._issue(CMD_VDU_GOTO, col & 0xFF, aux=row & 0xFF)

    def set_attr(self, attr: int) -> None:
        self._issue(CMD_VDU_ATTR, attr & 0xFF)

    def print(self, s: str) -> None:
        data = s.encode("ascii", errors="replace")
        if not data:
            return
        chunk = data[:248]
        self._issue(CMD_VDU_PRINT, len(chunk), buffer=chunk)

    def plot(self, x: int, y: int, color: int) -> None:
        c = color & 0xFFFF
        self._issue(CMD_GFX_PLOT, buffer=bytes([x & 0xFF, y & 0xFF, c & 0xFF, (c >> 8) & 0xFF]))

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        c = color & 0xFFFF
        self._issue(
            CMD_GFX_FILLRECT,
            buffer=bytes([x & 0xFF, y & 0xFF, w & 0xFF, h & 0xFF, c & 0xFF, (c >> 8) & 0xFF]),
        )

    def blit(self, x: int, y: int, pixels: bytes) -> None:
        payload = bytes([x & 0xFF, y & 0xFF]) + pixels
        self._issue(CMD_GFX_BLIT, len(payload) & 0xFF, buffer=payload)

    def vsync(self) -> None:
        self._issue(CMD_VDU_VSYNC)

    def status_ready(self) -> bool:
        return bool(self.bus.read_cpu(MB_STATUS) & ST_READY)

    def set_mode(self, mode: int = MODE_BOTH) -> None:
        from plover_vm.memory.vdu import CMD_VDU_MODE

        self._issue(CMD_VDU_MODE, mode & 0xFF)
