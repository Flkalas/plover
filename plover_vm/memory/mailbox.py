"""MMIO Mailbox @ $FF00 — 252 bytes."""

from __future__ import annotations

MB_BASE = 0xFF00
MB_STATUS = 0xFF00
MB_CMD = 0xFF01
MB_PARAM = 0xFF02
MB_BUFFER = 0xFF04

CMD_NOP = 0x00
CMD_READ = 0x01
CMD_WRITE = 0x02

ST_READY = 0x01
ST_BUSY = 0x02
ST_ERROR = 0x04


class Mailbox:
    def __init__(self) -> None:
        self._status = 0
        self._cmd = 0
        self._param = 0
        self._buffer = bytearray(248)
        self._sector = bytearray(512)

    def read(self, addr: int) -> int:
        a = addr & 0xFFFF
        if a == MB_STATUS:
            return self._status & 0xFF
        if a == MB_CMD:
            return self._cmd & 0xFF
        if a == MB_PARAM:
            return self._param & 0xFF
        if MB_BUFFER <= a <= 0xFFFB:
            return self._buffer[a - MB_BUFFER]
        return 0xFF

    def write(self, addr: int, val: int) -> None:
        a = addr & 0xFFFF
        v = val & 0xFF
        if a == MB_CMD:
            self._cmd = v
            self._handle_cmd()
        elif a == MB_PARAM:
            self._param = v
        elif MB_BUFFER <= a <= 0xFFFB:
            self._buffer[a - MB_BUFFER] = v

    def _handle_cmd(self) -> None:
        cmd = self._cmd
        if cmd == CMD_NOP:
            return
        if cmd == CMD_READ:
            self._status = ST_BUSY
            sector = self._param & 0xFF
            src = self._sector[sector * 512 : (sector + 1) * 512]
            self._buffer[:248] = src[:248]
            self._status = ST_READY
            self._cmd = CMD_NOP
        elif cmd == CMD_WRITE:
            self._status = ST_BUSY
            sector = self._param & 0xFF
            off = sector * 512
            self._sector[off : off + min(248, len(self._buffer))] = self._buffer[:248]
            self._status = ST_READY
            self._cmd = CMD_NOP
        else:
            self._status = ST_ERROR
            self._cmd = CMD_NOP

    def set_sector_stub(self, data: bytes) -> None:
        self._sector[: len(data)] = data[:512]
