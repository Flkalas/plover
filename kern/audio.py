"""Host-side audio driver — Mailbox APU wrapper."""

from __future__ import annotations

from plover_vm.memory.apu import CMD_APU_CH_OFF, CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, CMD_APU_SET_CTRL, WAVE_SQUARE
from plover_vm.memory.bus import MemoryBus
from plover_vm.memory.mailbox import MB_BUFFER, MB_CMD, MB_PARAM, MB_STATUS, ST_APU_READY

SIG_AUDIO = 0x41


class AudioDriver:
    def __init__(self, bus: MemoryBus) -> None:
        self.bus = bus

    def _issue(self, cmd: int, param: int = 0, *, buffer: bytes | bytearray | None = None) -> None:
        self.bus.write_cpu(MB_PARAM, param)
        if buffer is not None:
            for i, b in enumerate(buffer[:248]):
                self.bus.write_cpu(MB_BUFFER + i, b)
        self.bus.write_cpu(MB_CMD, cmd)

    def set_master(self, vol: int, *, mute: bool = False) -> None:
        self._issue(CMD_APU_SET_CTRL, buffer=bytes([vol & 0x0F, 1 if mute else 0]))

    def write_channel(self, ch: int, period: int, vol: int, wave: int) -> None:
        buf = bytes([ch & 0x03, period & 0xFF, (period >> 8) & 0xFF, vol & 0x0F, wave & 0x03])
        self._issue(CMD_APU_CH_WRITE, buffer=buf)

    def sync(self) -> None:
        self._issue(CMD_APU_CH_SYNC)

    def ch_off(self, ch: int) -> None:
        self._issue(CMD_APU_CH_OFF, ch & 0x03)

    def apu_ready(self) -> bool:
        return bool(self.bus.read_cpu(MB_STATUS) & ST_APU_READY)

    def beep(self, period: int, duration_frames: int) -> None:
        """Stage ch0 square tone, sync, store duration in ApuState.beep_ticks."""
        self.write_channel(0, period & 0xFFFF, 15, WAVE_SQUARE)
        self.sync()
        self.bus.mailbox.apu.beep_ticks = duration_frames & 0xFFFF
