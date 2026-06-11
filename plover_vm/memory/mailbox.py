"""MMIO Mailbox @ $FF00 — 252 bytes."""

from __future__ import annotations

from plover_vm.memory.apu import (
    CMD_APU_CH_OFF,
    CMD_APU_CH_SYNC,
    CMD_APU_CH_WRITE,
    CMD_APU_NOTE_OFF,
    CMD_APU_NOTE_ON,
    CMD_APU_SET_CTRL,
    CMD_APU_SYNC_ALT,
    CMD_APU_TRACK_CLEAR,
    ApuState,
)
from plover_vm.memory.hid import (
    CMD_HID_INJECT,
    CMD_HID_KEY_READ,
    CMD_HID_MOUSE_READ,
    CMD_HID_POLL,
    HidState,
)
from plover_vm.memory.vdu import (
    CMD_GFX_BLIT,
    CMD_GFX_CLS,
    CMD_GFX_FILLRECT,
    CMD_GFX_FRAME_FLUSH,
    CMD_GFX_GETPIX,
    CMD_GFX_HLINE,
    CMD_GFX_LAYER_CFG,
    CMD_GFX_OAM_HIDE,
    CMD_GFX_OAM_WRITE,
    CMD_GFX_PLOT,
    CMD_GFX_SET_TILE_PAL,
    CMD_GFX_SPR_KEY,
    CMD_GFX_TILE8,
    CMD_GFX_TILEMAP_SET,
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
ST_HID_KEY_PENDING = 0x10
ST_HID_MOUSE_PENDING = 0x20

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
        CMD_GFX_SET_TILE_PAL,
        CMD_GFX_LAYER_CFG,
        CMD_GFX_TILEMAP_SET,
        CMD_GFX_OAM_WRITE,
        CMD_GFX_OAM_HIDE,
        CMD_GFX_FRAME_FLUSH,
        CMD_GFX_SPR_KEY,
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
        CMD_APU_NOTE_ON,
        CMD_APU_NOTE_OFF,
        CMD_APU_TRACK_CLEAR,
        CMD_APU_SYNC_ALT,
    }
)

_HID_CMDS = frozenset(
    {
        CMD_HID_POLL,
        CMD_HID_KEY_READ,
        CMD_HID_MOUSE_READ,
        CMD_HID_INJECT,
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
        self._drive_banks: list[bytearray] = []
        self.vdu = VduState()
        self.apu = ApuState()
        self.hid = HidState()
        self._apu_ready = True
        self._vfdd_busy = False

    def _status_byte(self) -> int:
        base = self._status & 0xFF
        if self._apu_ready:
            base |= ST_APU_READY
        if self.hid.key_pending:
            base |= ST_HID_KEY_PENDING
        if self.hid.mouse_pending:
            base |= ST_HID_MOUSE_PENDING
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

    def _handle_hid(self, cmd: int) -> None:
        if self._vfdd_busy or (self._status & ST_BUSY):
            return
        self.hid.dispatch(cmd, self._buffer)

    def _handle_cmd(self) -> None:
        cmd = self._cmd
        if cmd == CMD_NOP:
            return
        if cmd == CMD_READ:
            self._vfdd_busy = True
            self._status = ST_BUSY
            drive_id = self._aux & 0xFF
            sector = self._param & 0xFF
            view = self._sector_view(drive_id, sector)
            if view is not None:
                n = min(len(view), 248)
                self._buffer[:n] = view[:n]
                self._vfdd_busy = False
                self._status = ST_READY
            else:
                self._vfdd_busy = False
                self._status = ST_ERROR
            self._cmd = CMD_NOP
        elif cmd == CMD_WRITE:
            self._vfdd_busy = True
            self._status = ST_BUSY
            drive_id = self._aux & 0xFF
            sector = self._param & 0xFF
            if drive_id < len(self._drive_banks):
                bank = self._drive_banks[drive_id]
                off = sector * 512
                if off < len(bank):
                    n = min(248, len(bank) - off)
                    bank[off : off + n] = self._buffer[:n]
                    self._vfdd_busy = False
                    self._status = ST_READY
                else:
                    self._vfdd_busy = False
                    self._status = ST_ERROR
            else:
                self._vfdd_busy = False
                self._status = ST_ERROR
            self._cmd = CMD_NOP
        elif cmd in _HID_CMDS:
            self._handle_hid(cmd)
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

    def register_drive_bank(self, drive_id: int, data: bytes) -> None:
        while len(self._drive_banks) <= drive_id:
            self._drive_banks.append(bytearray())
        self._drive_banks[drive_id] = bytearray(data)
        if drive_id == 0 and data:
            self._sector[: min(len(data), 512)] = data[:512]

    def _sector_view(self, drive_id: int, sector: int) -> memoryview | None:
        if drive_id >= len(self._drive_banks):
            return None
        bank = self._drive_banks[drive_id]
        start = sector * 512
        if start >= len(bank):
            return None
        end = min(start + 512, len(bank))
        return memoryview(bank)[start:end]

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

    def issue_hid(
        self,
        cmd: int,
        param: int = 0,
        *,
        buffer: bytes | bytearray | None = None,
    ) -> None:
        """Host helper: prime PARAM/BUFFER and dispatch one HID command."""
        self._param = param & 0xFF
        if buffer is not None:
            self._buffer[: len(buffer)] = buffer[:248]
        self._cmd = cmd & 0xFF
        self._handle_cmd()
