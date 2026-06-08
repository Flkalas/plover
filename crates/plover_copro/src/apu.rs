pub const CMD_APU_SET_CTRL: u8 = 0x50;
pub const CMD_APU_CH_WRITE: u8 = 0x51;
pub const CMD_APU_CH_SYNC: u8 = 0x52;
pub const CMD_APU_CH_OFF: u8 = 0x53;

pub const APU_CHANNELS: usize = 4;
pub const NOISE_CHANNEL: usize = 3;

pub const WAVE_OFF: u8 = 0;
pub const WAVE_SQUARE: u8 = 1;
pub const WAVE_NOISE: u8 = 2;

pub const CLK_HZ: u32 = 44_100;
pub const SAMPLE_RATE: u32 = 22_050;

#[derive(Clone, Copy, Default, Debug, PartialEq, Eq)]
pub struct Channel {
    pub period: u16,
    pub volume: u8,
    pub wave: u8,
}

#[derive(Clone, Debug)]
pub struct ApuState {
    pub channels: [Channel; APU_CHANNELS],
    pub pending: [Channel; APU_CHANNELS],
    pub master_vol: u8,
    pub mute: bool,
    pub beep_ticks: u16,
    pub clk_hz: u32,
    pub sample_rate: u32,
    phase: [u32; APU_CHANNELS],
    lfsr: u16,
}

impl Default for ApuState {
    fn default() -> Self {
        Self {
            channels: [Channel::default(); APU_CHANNELS],
            pending: [Channel::default(); APU_CHANNELS],
            master_vol: 15,
            mute: false,
            beep_ticks: 0,
            clk_hz: CLK_HZ,
            sample_rate: SAMPLE_RATE,
            phase: [0; APU_CHANNELS],
            lfsr: 0x7FFF,
        }
    }
}

impl ApuState {
    pub fn set_ctrl(&mut self, buffer: &[u8]) -> bool {
        if buffer.len() < 2 {
            return false;
        }
        self.master_vol = buffer[0] & 0x0F;
        self.mute = (buffer[1] & 0x01) != 0;
        true
    }

    pub fn stage_ch_write(&mut self, buffer: &[u8]) -> bool {
        if buffer.len() < 5 {
            return false;
        }
        let ch = (buffer[0] & 0x03) as usize;
        let period = u16::from(buffer[1]) | (u16::from(buffer[2]) << 8);
        let vol = buffer[3] & 0x0F;
        let wave = buffer[4] & 0x03;
        if ch == NOISE_CHANNEL {
            if wave != WAVE_OFF && wave != WAVE_NOISE {
                return false;
            }
        } else if wave != WAVE_OFF && wave != WAVE_SQUARE {
            return false;
        }
        self.pending[ch] = Channel {
            period,
            volume: vol,
            wave,
        };
        true
    }

    pub fn sync(&mut self) -> bool {
        for i in 0..APU_CHANNELS {
            self.channels[i] = self.pending[i];
            self.phase[i] = 0;
        }
        true
    }

    pub fn ch_off(&mut self, ch: usize) -> bool {
        if ch >= APU_CHANNELS {
            return false;
        }
        let off = Channel::default();
        self.channels[ch] = off;
        self.pending[ch] = off;
        self.phase[ch] = 0;
        true
    }

    pub fn dispatch(&mut self, cmd: u8, param: u8, buffer: &mut [u8; 248]) -> bool {
        match cmd {
            CMD_APU_SET_CTRL => self.set_ctrl(buffer),
            CMD_APU_CH_WRITE => self.stage_ch_write(buffer),
            CMD_APU_CH_SYNC => self.sync(),
            CMD_APU_CH_OFF => self.ch_off((param & 0x03) as usize),
            _ => false,
        }
    }

    pub fn mix_samples(&mut self, n: usize) -> Vec<u8> {
        let mut out = vec![128u8; n];
        if self.mute {
            return out;
        }
        let masters = (self.master_vol.max(1) as f32) / 15.0;
        let tick_step = self.clk_hz / self.sample_rate;
        for sample in out.iter_mut() {
            let mut acc = 0.0f32;
            for ch in 0..APU_CHANNELS {
                let c = &self.channels[ch];
                if c.wave == WAVE_OFF || c.volume == 0 || c.period == 0 {
                    continue;
                }
                if c.wave == WAVE_SQUARE {
                    let tick = self.phase[ch];
                    if c.period > 0 && ((tick / u32::from(c.period)) % 2) == 0 {
                        acc += f32::from(c.volume);
                    }
                    let period2 = u32::from(c.period) * 2;
                    self.phase[ch] = if period2 > 0 {
                        (tick + tick_step) % period2
                    } else {
                        0
                    };
                } else if c.wave == WAVE_NOISE && ch == NOISE_CHANNEL {
                    let bit = self.lfsr & 1;
                    self.lfsr = (self.lfsr >> 1)
                        | (((bit ^ ((self.lfsr >> 1) & 1)) as u16) << 14);
                    if bit != 0 {
                        acc += f32::from(c.volume);
                    }
                }
            }
            let level = 128.0 + (acc / (APU_CHANNELS as f32 * 15.0)) * 127.0 * masters;
            *sample = level.round().clamp(0.0, 255.0) as u8;
        }
        out
    }

    pub fn zero_crossings(samples: &[u8]) -> usize {
        let mut crosses = 0;
        let mut prev = i16::from(samples[0]) - 128;
        for &b in &samples[1..] {
            let cur = i16::from(b) - 128;
            if (prev > 0 && cur <= 0) || (prev <= 0 && cur > 0) {
                crosses += 1;
            }
            prev = cur;
        }
        crosses
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn buf5(data: [u8; 5]) -> [u8; 248] {
        let mut b = [0u8; 248];
        b[..5].copy_from_slice(&data);
        b
    }

    #[test]
    fn apu_set_ctrl() {
        let mut apu = ApuState::default();
        assert!(apu.dispatch(CMD_APU_SET_CTRL, 0, &mut buf5([10, 0, 0, 0, 0])));
        assert_eq!(apu.master_vol, 10);
        assert!(!apu.mute);
        assert!(apu.dispatch(CMD_APU_SET_CTRL, 0, &mut buf5([5, 1, 0, 0, 0])));
        assert_eq!(apu.master_vol, 5);
        assert!(apu.mute);
    }

    #[test]
    fn apu_ch_write_sync() {
        let mut apu = ApuState::default();
        assert!(apu.dispatch(CMD_APU_CH_WRITE, 0, &mut buf5([0, 22, 0, 15, WAVE_SQUARE])));
        assert_eq!(apu.channels[0].period, 0);
        assert!(apu.dispatch(CMD_APU_CH_SYNC, 0, &mut [0u8; 248]));
        assert_eq!(apu.channels[0].period, 22);
        assert_eq!(apu.channels[0].volume, 15);
    }

    #[test]
    fn apu_ch_off() {
        let mut apu = ApuState::default();
        apu.dispatch(CMD_APU_CH_WRITE, 0, &mut buf5([0, 30, 0, 10, WAVE_SQUARE]));
        apu.dispatch(CMD_APU_CH_SYNC, 0, &mut [0u8; 248]);
        assert!(apu.dispatch(CMD_APU_CH_OFF, 0, &mut [0u8; 248]));
        assert_eq!(apu.channels[0].period, 0);
        assert_eq!(apu.channels[0].wave, WAVE_OFF);
    }

    #[test]
    fn apu_ch3_noise_only() {
        let mut apu = ApuState::default();
        assert!(apu.dispatch(CMD_APU_CH_WRITE, 0, &mut buf5([3, 10, 0, 8, WAVE_NOISE])));
        assert!(!apu.dispatch(CMD_APU_CH_WRITE, 0, &mut buf5([3, 10, 0, 8, WAVE_SQUARE])));
        apu.dispatch(CMD_APU_CH_SYNC, 0, &mut [0u8; 248]);
        assert_eq!(apu.channels[3].wave, WAVE_NOISE);
    }
}
