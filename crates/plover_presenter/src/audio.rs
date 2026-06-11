use plover_copro::ApuState;
use std::sync::{Arc, Mutex};

/// cpal output stream on the creating thread (required on Windows WASAPI).
pub struct AudioBridge {
    _stream: cpal::Stream,
}

impl AudioBridge {
    pub fn start(apu: Arc<Mutex<ApuState>>) -> Result<Self, String> {
        use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
        use cpal::SampleFormat;

        let host = cpal::default_host();
        let device = host
            .default_output_device()
            .ok_or_else(|| "no audio output device".to_string())?;
        let config = device
            .default_output_config()
            .map_err(|e| e.to_string())?;
        let sample_rate = config.sample_rate().0;
        let apu_cb = apu.clone();

        let stream = match config.sample_format() {
            SampleFormat::F32 => {
                let cfg: cpal::StreamConfig = config.into();
                device
                    .build_output_stream(
                        &cfg,
                        move |data: &mut [f32], _| write_f32(&apu_cb, sample_rate, data),
                        |e| eprintln!("audio stream error: {e}"),
                        None,
                    )
                    .map_err(|e| e.to_string())?
            }
            SampleFormat::I16 => {
                let cfg: cpal::StreamConfig = config.into();
                device
                    .build_output_stream(
                        &cfg,
                        move |data: &mut [i16], _| write_i16(&apu_cb, sample_rate, data),
                        |e| eprintln!("audio stream error: {e}"),
                        None,
                    )
                    .map_err(|e| e.to_string())?
            }
            SampleFormat::U8 => {
                let cfg: cpal::StreamConfig = config.into();
                device
                    .build_output_stream(
                        &cfg,
                        move |data: &mut [u8], _| write_u8(&apu_cb, sample_rate, data),
                        |e| eprintln!("audio stream error: {e}"),
                        None,
                    )
                    .map_err(|e| e.to_string())?
            }
            other => {
                return Err(format!("unsupported cpal sample format: {other:?}"));
            }
        };

        stream.play().map_err(|e| e.to_string())?;
        Ok(Self { _stream: stream })
    }
}

fn write_u8(apu: &Arc<Mutex<ApuState>>, sample_rate: u32, data: &mut [u8]) {
    if let Ok(mut a) = apu.lock() {
        a.sample_rate = sample_rate;
        let mixed = a.mix_samples(data.len());
        data.copy_from_slice(&mixed);
    } else {
        data.fill(128);
    }
}

fn write_f32(apu: &Arc<Mutex<ApuState>>, sample_rate: u32, data: &mut [f32]) {
    if let Ok(mut a) = apu.lock() {
        a.sample_rate = sample_rate;
        let mixed = a.mix_samples(data.len());
        for (out, sample) in data.iter_mut().zip(mixed.iter()) {
            *out = (f32::from(*sample) - 128.0) / 128.0;
        }
    } else {
        data.fill(0.0);
    }
}

fn write_i16(apu: &Arc<Mutex<ApuState>>, sample_rate: u32, data: &mut [i16]) {
    if let Ok(mut a) = apu.lock() {
        a.sample_rate = sample_rate;
        let mixed = a.mix_samples(data.len());
        for (out, sample) in data.iter_mut().zip(mixed.iter()) {
            let norm = (f32::from(*sample) - 128.0) / 128.0;
            *out = (norm * i16::MAX as f32) as i16;
        }
    } else {
        data.fill(0);
    }
}
