use crate::compose::{compose_rgb, upscale_nearest_2x};
use plover_copro::VduState;

pub struct HeadlessPresenter {
    pub last_frame: Vec<u8>,
    hold_counter: u8,
    last_vdu_frame: u32,
}

impl Default for HeadlessPresenter {
    fn default() -> Self {
        Self {
            last_frame: vec![0; 640 * 480 * 3],
            hold_counter: 0,
            last_vdu_frame: 0,
        }
    }
}

impl HeadlessPresenter {
    /// Update on 60Hz tick; returns true if pixels changed.
    pub fn tick(&mut self, vdu: &VduState) -> bool {
        if vdu.frame != self.last_vdu_frame {
            self.last_vdu_frame = vdu.frame;
            let logical = compose_rgb(vdu);
            self.last_frame = upscale_nearest_2x(&logical);
            self.hold_counter = 2;
            return true;
        }
        if self.hold_counter > 0 {
            self.hold_counter -= 1;
        }
        false
    }

    pub fn pixels(&self) -> &[u8] {
        &self.last_frame
    }
}
