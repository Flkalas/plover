#[cfg(feature = "sdl")]
use sdl2::event::Event;
#[cfg(feature = "sdl")]
use sdl2::keyboard::Keycode;
#[cfg(feature = "sdl")]
use sdl2::pixels::PixelFormatEnum;

use crate::compose::{compose_rgb, upscale_nearest_2x, OUTPUT_H, OUTPUT_W};
use crate::HidBridge;
use plover_copro::Mailbox;
use plover_copro::VduState;

pub struct SdlPresenter {
    _ctx: sdl2::Sdl,
    canvas: sdl2::render::Canvas<sdl2::render::Window>,
    texture: sdl2::render::Texture,
    last_vdu_frame: u32,
}

impl SdlPresenter {
    pub fn new(title: &str) -> Result<Self, String> {
        let ctx = sdl2::init().map_err(|e| e.to_string())?;
        let video = ctx.video().map_err(|e| e.to_string())?;
        let window = video
            .window(title, OUTPUT_W as u32, OUTPUT_H as u32)
            .map_err(|e| e.to_string())?;
        let mut canvas = window.into_canvas().build().map_err(|e| e.to_string())?;
        let texture_creator = canvas.texture_creator();
        let texture = texture_creator
            .create_texture_streaming(PixelFormatEnum::RGB24, OUTPUT_W as u32, OUTPUT_H as u32)
            .map_err(|e| e.to_string())?;
        Ok(Self {
            _ctx: ctx,
            canvas,
            texture,
            last_vdu_frame: 0,
        })
    }

    pub fn pump_events(&self, mb: &mut Mailbox) -> bool {
        let mut quit = false;
        let mut event_pump = self._ctx.event_pump().unwrap();
        for event in event_pump.poll_iter() {
            match event {
                Event::Quit { .. } => quit = true,
                Event::KeyDown { keycode: Some(k), .. } => {
                    if let Some(ch) = keycode_to_ascii(k) {
                        HidBridge::inject_key(mb, ch);
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

    pub fn present(&mut self, vdu: &VduState) -> Result<(), String> {
        if vdu.frame != self.last_vdu_frame {
            self.last_vdu_frame = vdu.frame;
            let logical = compose_rgb(vdu);
            let frame = upscale_nearest_2x(&logical);
            texture_update(&mut self.texture, &frame)?;
        }
        self.canvas
            .copy(&self.texture, None, None)
            .map_err(|e| e.to_string())?;
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

fn keycode_to_ascii(k: Keycode) -> Option<u8> {
    match k {
        Keycode::A => Some(b'a'),
        Keycode::B => Some(b'b'),
        Keycode::H => Some(b'H'),
        Keycode::Return => Some(b'\n'),
        Keycode::Space => Some(b' '),
        _ => None,
    }
}
