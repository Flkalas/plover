#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Alu16Result {
    pub y: u16,
    pub cout: bool,
    pub zero: bool,
}

pub fn add16(a: u16, b: u16) -> Alu16Result {
    let s = u32::from(a) + u32::from(b);
    let y = (s & 0xFFFF) as u16;
    Alu16Result {
        y,
        cout: s > 0xFFFF,
        zero: y == 0,
    }
}

pub fn cmp16_u(a: u16, b: u16) -> Alu16Result {
    let s = u32::from(a).wrapping_sub(u32::from(b));
    let y = (s & 0xFFFF) as u16;
    Alu16Result {
        y,
        cout: a >= b,
        zero: y == 0,
    }
}
