"""MMIO Mailbox @ $FF00 — 252 bytes."""

from __future__ import annotations

from plover_vm.memory.apu import (
    CMD_APU_CH_OFF,
    CMD_APU_CH_SYNC,
    CMD_APU_CH_WRITE,
    CMD_APU_SET_CTRL,
    ApuState,
)
from plover_vm.memory.vdu import (
    CMD_GFX_BLIT,
    CMD_GFX_CLS,
    CMD_GFX_FILLRECT,
    CMD_GFX_GETPIX,
    CMD_GFX_HLINE,
    CMD_GFX_PLOT,
    CMD_GFX_TILE8,
    CMD_VDU_ATTR,
    CMD_VDU_CLS,
    CMD_VDU_CURSORGET,
    CMD_VDU_GOTO,
    CMD_VDU_MODE,
    CMD_VDU_PAL_TEXT,
    CMD_VDU_PRINT,
    CMD_VDU_PUTCH,
    CMD_VDU_SCROLL,
    CMD_VDU_VSYNC,
    VduState,
)

MB_BASE = 0xFF00
MB_STATUS = 0xFF00
MB_CMD = 0xFF01
MB_PARAM = 0xFF02
MB_AUX = 0xFF03
MB_BUFFER = 0xFF04

CMD_NOP = 0x00
CMD_READ = 0x01
CMD_WRITE = 0x02

ST_READY = 0x01
ST_BUSY = 0x02
ST_ERROR = 0x04
ST_APU_READY = 0x08

_VDU_CMDS = frozenset(
    {
        CMD_VDU_CLS,
        CMD_VDU_PUTCH,
        CMD_VDU_GOTO,
        CMD_VDU_ATTR,
        CMD_VDU_PRINT,
        CMD_VDU_SCROLL,
        CMD_VDU_CURSORGET,
        CMD_VDU_PAL_TEXT,
        CMD_GFX_CLS,
        CMD_GFX_PLOT,
        CMD_GFX_HLINE,
        CMD_GFX_FILLRECT,
        CMD_GFX_BLIT,
        CMD_GFX_GETPIX,
        CMD_GFX_TILE8,
        CMD_VDU_VSYNC,
        CMD_VDU_MODE,
    }
)

_APU_CMDS = frozenset(
    {
        CMD_APU_SET_CTRL,
        CMD_APU_CH_WRITE,
        CMD_APU_CH_SYNC,
        CMD_APU_CH_OFF,
    }
)


class Mailbox:
    def __init__(self) -> None:
        self._status = 0
        self._cmd = 0
        self._param = 0
        self._aux = 0
        self._buffer = bytearray(248)
        self._sector = bytearray(512)
        self.vdu = VduState()
        self.apu = ApuState()
        self._apu_ready = True
        self._vfdd_busy = False

    def _status_byte(self) -> int:
        base = self._status & 0xFF
        if self._apu_ready:
            base |= ST_APU_READY
        return base & 0xFF

    def read(self, addr: int) -> int:
        a = addr & 0xFFFF
        if a == MB_STATUS:
            return self._status_byte()
        if a == MB_CMD:
            return self._cmd & 0xFF
        if a == MB_PARAM:
            return self._param & 0xFF
        if a == MB_AUX:
            return self._aux & 0xFF
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
        elif a == MB_AUX:
            self._aux = v
        elif MB_BUFFER <= a <= 0xFFFB:
            self._buffer[a - MB_BUFFER] = v

    def _handle_apu(self, cmd: int) -> None:
        if self._vfdd_busy or (self._status & ST_BUSY):
            return
        if self.apu.dispatch(cmd, self._param, self._buffer):
            self._apu_ready = True

    def _handle_cmd(self) -> None:
        cmd = self._cmd
        if cmd == CMD_NOP:
            return
        if cmd == CMD_READ:
            self._vfdd_busy = True
            self._status = ST_BUSY
            sector = self._param & 0xFF
            src = self._sector[sector * 512 : (sector + 1) * 512]
            self._buffer[:248] = src[:248]
            self._vfdd_busy = False
            self._status = ST_READY
            self._cmd = CMD_NOP
        elif cmd == CMD_WRITE:
            self._vfdd_busy = True
            self._status = ST_BUSY
            sector = self._param & 0xFF
            off = sector * 512
            self._sector[off : off + min(248, len(self._buffer))] = self._buffer[:248]
            self._vfdd_busy = False
            self._status = ST_READY
            self._cmd = CMD_NOP
        elif cmd in _APU_CMDS:
            self._handle_apu(cmd)
            self._cmd = CMD_NOP
        elif cmd in _VDU_CMDS:
            self._status = ST_BUSY
            self.vdu.dispatch(cmd, self._param, self._aux, self._buffer)
            if self.vdu.last_error:
                self._status = ST_ERROR
            else:
                self._status = ST_READY
            self._cmd = CMD_NOP
        else:
            self._status = ST_ERROR
            self._cmd = CMD_NOP

    def set_sector_stub(self, data: bytes) -> None:
        self._sector[: len(data)] = data[:512]

    def issue_vdu(
        self,
        cmd: int,
        param: int = 0,
        *,
        aux: int = 0,
        buffer: bytes | bytearray | None = None,
    ) -> None:
        """Host helper: prime PARAM/AUX/BUFFER and dispatch one VDU/GFX command."""
        self._param = param & 0xFF
        self._aux = aux & 0xFF
        if buffer is not None:
            self._buffer[: len(buffer)] = buffer[:248]
        self._cmd = cmd & 0xFF
        self._handle_cmd()

    def issue_apu(
        self,
        cmd: int,
        param: int = 0,
        *,
        buffer: bytes | bytearray | None = None,
    ) -> None:
        """Host helper: prime PARAM/BUFFER and dispatch one APU command."""
        self._param = param & 0xFF
        if buffer is not None:
            self._buffer[: len(buffer)] = buffer[:248]
        self._cmd = cmd & 0xFF
        self._handle_cmd()
