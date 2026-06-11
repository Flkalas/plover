use crate::runtime::{period_for_hz, BasicRuntime};
use crate::tokens::*;
use plover_mmu::MemoryBus;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BasicVmError {
    UnknownOpcode(u8),
    End,
}

pub struct BasicVm {
    pub ip: u16,
    pub running: bool,
}

impl Default for BasicVm {
    fn default() -> Self {
        Self {
            ip: TOK_BASE,
            running: true,
        }
    }
}

impl BasicVm {
    pub fn new() -> Self {
        Self::default()
    }

    fn read_u8(bus: &MemoryBus, addr: u16) -> u8 {
        bus.read_cpu(addr)
    }

    fn read_u16_le(bus: &MemoryBus, addr: u16) -> u16 {
        let lo = u32::from(Self::read_u8(bus, addr));
        let hi = u32::from(Self::read_u8(bus, addr.wrapping_add(1)));
        (lo | (hi << 8)) as u16
    }

    fn var_get(bus: &MemoryBus, idx: usize) -> u8 {
        Self::read_u8(bus, var_addr(idx))
    }

    fn var_set(bus: &mut MemoryBus, idx: usize, val: u8) {
        bus.write_cpu(var_addr(idx), val);
    }

    pub fn step(&mut self, bus: &mut MemoryBus) -> Result<(), BasicVmError> {
        if !self.running {
            return Err(BasicVmError::End);
        }
        let op = Self::read_u8(bus, self.ip);
        self.ip = self.ip.wrapping_add(1);
        let mut rt = BasicRuntime::new(bus);
        match op {
            TOK_END => {
                self.running = false;
                Err(BasicVmError::End)
            }
            TOK_CLS => {
                rt.cls();
                Ok(())
            }
            TOK_PRINT_STR => {
                let len = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let mut s = String::new();
                for i in 0..len {
                    let ch = Self::read_u8(rt.bus, self.ip.wrapping_add(i as u16));
                    if ch.is_ascii() {
                        s.push(ch as char);
                    }
                }
                self.ip = self.ip.wrapping_add(len as u16);
                rt.print_str(&s);
                Ok(())
            }
            TOK_LET_IMM => {
                let var = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let val = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                Self::var_set(rt.bus, var, val);
                Ok(())
            }
            TOK_GOTO => {
                let target = Self::read_u16_le(rt.bus, self.ip);
                self.ip = target;
                Ok(())
            }
            TOK_INKEY_VAR => {
                let var = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let key = rt.inkey();
                Self::var_set(rt.bus, var, key);
                Ok(())
            }
            TOK_IF_KEY_NEQ => {
                let key = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let target = Self::read_u16_le(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(2);
                if rt.inkey() != key {
                    self.ip = target;
                }
                Ok(())
            }
            TOK_ADD_VAR_IMM => {
                let var = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let delta = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let cur = Self::var_get(rt.bus, var);
                Self::var_set(rt.bus, var, cur.wrapping_add(delta));
                Ok(())
            }
            TOK_SPRITE_VAR => {
                let id = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let vx = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let vy = Self::read_u8(rt.bus, self.ip) as usize;
                self.ip = self.ip.wrapping_add(1);
                let tile = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let pal = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                rt.sprite_set(
                    id,
                    Self::var_get(rt.bus, vx),
                    Self::var_get(rt.bus, vy),
                    tile,
                    pal,
                );
                Ok(())
            }
            TOK_DRAW => {
                rt.draw();
                Ok(())
            }
            TOK_SOUND => {
                let ch = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let hz = Self::read_u16_le(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(2);
                let dur = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                rt.sound(ch, period_for_hz(u32::from(hz)), u16::from(dur) * 10);
                Ok(())
            }
            TOK_LAYER_SCROLL => {
                let layer = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let sx = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let sy = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                rt.layer_scroll(layer, sx, sy);
                Ok(())
            }
            TOK_TILE => {
                let layer = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let tx = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let ty = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                let tile_id = Self::read_u8(rt.bus, self.ip);
                self.ip = self.ip.wrapping_add(1);
                rt.tile_set(layer, tx, ty, tile_id);
                Ok(())
            }
            other => Err(BasicVmError::UnknownOpcode(other)),
        }
    }

    pub fn run_steps(&mut self, bus: &mut MemoryBus, max: usize) -> Result<(), BasicVmError> {
        for _ in 0..max {
            match self.step(bus) {
                Ok(()) => {}
                Err(BasicVmError::End) => return Err(BasicVmError::End),
                Err(e @ BasicVmError::UnknownOpcode(_)) => return Err(e),
            }
        }
        Ok(())
    }
}
