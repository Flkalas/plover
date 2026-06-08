use plover_copro::ApuState;
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

/// cpal output stream at device sample rate; mixes from shared `ApuState`.
pub struct AudioBridge {
    _thread: JoinHandle<()>,
}

impl AudioBridge {
    pub fn start(apu: Arc<Mutex<ApuState>>) -> Result<Self, String> {
        use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};

        let host = cpal::default_host();
        let device = host
            .default_output_device()
            .ok_or_else(|| "no audio output device".to_string())?;
        let config = device
            .default_output_config()
            .map_err(|e| e.to_string())?;
        if config.sample_format() != cpal::SampleFormat::U8 {
            return Err("expected U8 output format".into());
        }
        let sample_rate = config.sample_rate().0;
        let apu_cb = apu.clone();
        let stream = device
            .build_output_stream(
                &config.into(),
                move |data: &mut [u8], _| {
                    if let Ok(mut a) = apu_cb.lock() {
                        a.sample_rate = sample_rate;
                        let mixed = a.mix_samples(data.len());
                        data.copy_from_slice(&mixed);
                    } else {
                        data.fill(128);
                    }
                },
                |e| eprintln!("audio stream error: {e}"),
                None,
            )
            .map_err(|e| e.to_string())?;

        let thread = std::thread::spawn(move || {
            if let Err(e) = stream.play() {
                eprintln!("audio play failed: {e}");
                return;
            }
            loop {
                std::thread::sleep(std::time::Duration::from_secs(3600));
            }
        });

        Ok(Self { _thread: thread })
    }
}
