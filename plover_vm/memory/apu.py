"""APU PSG state for Mailbox audio commands (4ch square/noise)."""

from __future__ import annotations

from dataclasses import dataclass, field

CMD_APU_SET_CTRL = 0x50
CMD_APU_CH_WRITE = 0x51
CMD_APU_CH_SYNC = 0x52
CMD_APU_CH_OFF = 0x53

APU_CHANNELS = 4
NOISE_CHANNEL = 3

WAVE_OFF = 0
WAVE_SQUARE = 1
WAVE_NOISE = 2

CLK_HZ = 44_100
SAMPLE_RATE = 22_050


@dataclass
class Channel:
    period: int = 0
    volume: int = 0
    wave: int = WAVE_OFF

    def copy(self) -> Channel:
        return Channel(period=self.period, volume=self.volume, wave=self.wave)


@dataclass
class ApuState:
    """4ch PSG; staged writes commit on APU_CH_SYNC."""

    channels: list[Channel] = field(default_factory=lambda: [Channel() for _ in range(APU_CHANNELS)])
    pending: list[Channel] = field(default_factory=lambda: [Channel() for _ in range(APU_CHANNELS)])
    master_vol: int = 15
    mute: bool = False
    beep_ticks: int = 0
    clk_hz: int = CLK_HZ
    sample_rate: int = SAMPLE_RATE
    _phase: list[int] = field(default_factory=lambda: [0] * APU_CHANNELS)
    _lfsr: int = 0x7FFF

    def set_ctrl(self, buffer: bytearray | bytes) -> bool:
        if len(buffer) < 2:
            return False
        self.master_vol = buffer[0] & 0x0F
        self.mute = bool(buffer[1] & 0x01)
        return True

    def stage_ch_write(self, buffer: bytearray | bytes) -> bool:
        if len(buffer) < 5:
            return False
        ch = buffer[0] & 0x03
        period = buffer[1] | (buffer[2] << 8)
        vol = buffer[3] & 0x0F
        wave = buffer[4] & 0x03
        if ch == NOISE_CHANNEL:
            if wave not in (WAVE_OFF, WAVE_NOISE):
                return False
        elif wave not in (WAVE_OFF, WAVE_SQUARE):
            return False
        self.pending[ch] = Channel(period=period & 0xFFFF, volume=vol, wave=wave)
        return True

    def sync(self) -> bool:
        for i in range(APU_CHANNELS):
            self.channels[i] = self.pending[i].copy()
            self._phase[i] = 0
        return True

    def ch_off(self, ch: int) -> bool:
        if ch < 0 or ch >= APU_CHANNELS:
            return False
        off = Channel()
        self.channels[ch] = off.copy()
        self.pending[ch] = off.copy()
        self._phase[ch] = 0
        return True

    def dispatch(self, cmd: int, param: int, buffer: bytearray) -> bool:
        """Return True if command accepted, False if silent drop."""
        if cmd == CMD_APU_SET_CTRL:
            return self.set_ctrl(buffer)
        if cmd == CMD_APU_CH_WRITE:
            return self.stage_ch_write(buffer)
        if cmd == CMD_APU_CH_SYNC:
            return self.sync()
        if cmd == CMD_APU_CH_OFF:
            return self.ch_off(param & 0x03)
        return False

    def freq_hz(self, ch: int) -> float:
        c = self.channels[ch]
        if c.period <= 0 or c.wave == WAVE_OFF:
            return 0.0
        return self.clk_hz / (2.0 * c.period)

    def mix_samples(self, n: int) -> bytes:
        """Generate n mono 8-bit samples (center 128) for VM tests."""
        out = bytearray(n)
        if self.mute:
            return bytes([128] * n)
        masters = max(1, self.master_vol) / 15.0
        tick_step = self.clk_hz // self.sample_rate
        for i in range(n):
            acc = 0.0
            for ch in range(APU_CHANNELS):
                c = self.channels[ch]
                if c.wave == WAVE_OFF or c.volume == 0 or c.period <= 0:
                    continue
                if c.wave == WAVE_SQUARE:
                    tick = self._phase[ch]
                    if ((tick // c.period) % 2) == 0:
                        acc += c.volume
                    self._phase[ch] = (tick + tick_step) % (c.period * 2)
                elif c.wave == WAVE_NOISE and ch == NOISE_CHANNEL:
                    bit = self._lfsr & 1
                    self._lfsr = (self._lfsr >> 1) | ((bit ^ ((self._lfsr >> 1) & 1)) << 14)
                    if bit:
                        acc += c.volume
            level = 128 + int((acc / (APU_CHANNELS * 15.0)) * 127.0 * masters)
            out[i] = max(0, min(255, level)) & 0xFF
        return bytes(out)

    def zero_crossings(self, samples: bytes) -> int:
        """Count approximate zero-crossings around 128 for tone tests."""
        crosses = 0
        prev = samples[0] - 128
        for b in samples[1:]:
            cur = b - 128
            if (prev > 0 and cur <= 0) or (prev <= 0 and cur > 0):
                crosses += 1
            prev = cur
        return crosses
