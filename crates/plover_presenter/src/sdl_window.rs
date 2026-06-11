#[cfg(feature = "sdl")]
use sdl2::event::Event;
#[cfg(feature = "sdl")]
use sdl2::keyboard::Keycode;
#[cfg(feature = "sdl")]
use sdl2::pixels::PixelFormatEnum;
#[cfg(feature = "sdl")]
use sdl2::video::Window;

use crate::compose::{compose_rgb, upscale_nearest_2x, OUTPUT_H, OUTPUT_W};
use crate::HidBridge;
use plover_copro::Mailbox;
use plover_copro::VduState;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ShellInput {
    Continue,
    /// Draft changed (character typed or backspace).
    Edited,
    Submit,
    Quit,
}

pub struct SdlPresenter {
    _ctx: sdl2::Sdl,
    canvas: sdl2::render::Canvas<Window>,
    last_vdu_frame: u32,
}

impl SdlPresenter {
    pub fn new(title: &str) -> Result<Self, String> {
        let ctx = sdl2::init().map_err(|e| e.to_string())?;
        let video = ctx.video().map_err(|e| e.to_string())?;
        let window = video
            .window(title, OUTPUT_W as u32, OUTPUT_H as u32)
            .build()
            .map_err(|e| e.to_string())?;
        let canvas = window.into_canvas().build().map_err(|e| e.to_string())?;
        let _ = video.text_input().start();
        Ok(Self {
            _ctx: ctx,
            canvas,
            last_vdu_frame: 0,
        })
    }

    pub fn pump_events(&self, mb: &mut Mailbox) -> bool {
        let mut quit = false;
        let mut event_pump = self._ctx.event_pump().unwrap();
        for event in event_pump.poll_iter() {
            match event {
                Event::Quit { .. } => quit = true,
                Event::TextInput { text, .. } => {
                    for ch in text.chars() {
                        if ch.is_ascii() {
                            let b = ch as u8;
                            if b >= 0x20 || b == b'\n' || b == b'\r' || b == b'\t' {
                                HidBridge::inject_key(mb, b);
                            }
                        }
                    }
                }
                Event::MouseMotion { xrel, yrel, mousestate, .. } => {
                    let mut buttons = 0u8;
                    if mousestate.left() {
                        buttons |= 1;
                    }
                    if mousestate.right() {
                        buttons |= 2;
                    }
                    if mousestate.middle() {
                        buttons |= 4;
                    }
                    HidBridge::inject_mouse(mb, buttons, xrel as i8, yrel as i8);
                }
                _ => {}
            }
        }
        quit
    }

    /// Collect a shell command line from the focused window (TextInput + Backspace).
    pub fn pump_shell_input(&self, draft: &mut String) -> ShellInput {
        let mut event_pump = self._ctx.event_pump().unwrap();
        let mut result = ShellInput::Continue;
        for event in event_pump.poll_iter() {
            match event {
                Event::Quit { .. } => return ShellInput::Quit,
                Event::TextInput { text, .. } => {
                    for ch in text.chars() {
                        match ch {
                            '\r' | '\n' => result = ShellInput::Submit,
                            c if c.is_ascii() && !c.is_control() => {
                                draft.push(c);
                                result = ShellInput::Edited;
                            }
                            _ => {}
                        }
                    }
                }
                Event::KeyDown {
                    keycode: Some(Keycode::Return),
                    ..
                } => result = ShellInput::Submit,
                Event::KeyDown {
                    keycode: Some(Keycode::Backspace),
                    ..
                } => {
                    draft.pop();
                    result = ShellInput::Edited;
                }
                _ => {}
            }
        }
        result
    }

    pub fn present(&mut self, vdu: &VduState) -> Result<(), String> {
        if vdu.frame != self.last_vdu_frame {
            self.last_vdu_frame = vdu.frame;
            let logical = compose_rgb(vdu);
            let frame = upscale_nearest_2x(&logical);
            let texture_creator = self.canvas.texture_creator();
            let mut texture = texture_creator
                .create_texture_streaming(PixelFormatEnum::RGB24, OUTPUT_W as u32, OUTPUT_H as u32)
                .map_err(|e| e.to_string())?;
            texture_update(&mut texture, &frame)?;
            self.canvas
                .copy(&texture, None, None)
                .map_err(|e| e.to_string())?;
        }
        self.canvas.present();
        Ok(())
    }
}

fn texture_update(texture: &mut sdl2::render::Texture, rgb: &[u8]) -> Result<(), String> {
    texture
        .with_lock(None, |buf, pitch| {
            for y in 0..OUTPUT_H {
                for x in 0..OUTPUT_W {
                    let src = (y * OUTPUT_W + x) * 3;
                    let dst = y * pitch as usize + x * 3;
                    if dst + 2 < buf.len() && src + 2 < rgb.len() {
                        buf[dst] = rgb[src];
                        buf[dst + 1] = rgb[src + 1];
                        buf[dst + 2] = rgb[src + 2];
                    }
                }
            }
        })
        .map_err(|e| e.to_string())?;
    Ok(())
}
