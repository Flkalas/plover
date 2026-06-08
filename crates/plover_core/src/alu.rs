#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AluResult {
    pub y: u8,
    pub cout: bool,
    pub zero: bool,
}

pub fn alu8(a: u8, b: u8, alu_sel: u8) -> AluResult {
    let sel = alu_sel & 0x0F;
    let (y, cout) = match sel {
        0 => (0, false),
        1 => {
            let s = u16::from(a) + u16::from(b);
            ((s & 0xFF) as u8, s > 0xFF)
        }
        2 | 11 => {
            let s = u16::from(a) + u16::from(!b) + 1;
            ((s & 0xFF) as u8, s > 0xFF)
        }
        3 => (a & b, false),
        4 => (a | b, false),
        5 => (a ^ b, false),
        6 => (!a, false),
        7 => (a, false),
        8 => (b, false),
        9 => {
            let s = u16::from(a) + 1;
            ((s & 0xFF) as u8, s > 0xFF)
        }
        10 => {
            let s = u16::from(a) + 0xFF;
            ((s & 0xFF) as u8, s > 0xFF)
        }
        _ => (0, false),
    };
    AluResult {
        y,
        cout,
        zero: y == 0,
    }
}

pub fn apply_add(regs: [u8; 4], imm: u8) -> ([u8; 4], bool, bool) {
    let mut r = regs;
    if imm != 0 {
        r[1] = imm;
    }
    let res = alu8(r[0], r[1], 1);
    r[2] = res.y;
    (r, res.zero, res.cout)
}

pub fn apply_cmp_flags(regs: [u8; 4], imm: u8) -> (bool, bool) {
    let res = alu8(regs[0], imm, 2);
    (res.zero, res.cout)
}

pub fn apply_beq_compare(regs: [u8; 4], imm: u8) -> (bool, bool) {
    apply_cmp_flags(regs, imm)
}
