#[derive(Clone, Copy, Debug)]
pub struct ControlWord {
    pub raw: u16,
}

impl ControlWord {
    fn lo(self) -> u8 {
        (self.raw & 0xFF) as u8
    }

    pub fn reg_sel(self) -> u8 {
        ((self.raw >> 8) & 3) as u8
    }

    pub fn alu_op(self) -> u8 {
        (self.lo() >> 4) & 0xF
    }

    pub fn reg_we(self) -> bool {
        (self.lo() >> 3) & 1 != 0
    }

    pub fn y_oe(self) -> bool {
        (self.lo() >> 2) & 1 != 0
    }

    pub fn mem_rd(self) -> bool {
        (self.lo() >> 1) & 1 != 0
    }

    pub fn mem_wr(self) -> bool {
        self.lo() & 1 != 0
    }
}

pub fn cs_index(opcode: u8, phase: u8) -> usize {
    ((opcode & 0xF) as usize) << 2 | (phase & 3) as usize
}

pub fn lookup_cw(mut nor_read: impl FnMut(usize) -> u16, opcode: u8, phase: u8) -> ControlWord {
    let idx = cs_index(opcode, phase);
    ControlWord {
        raw: nor_read(idx),
    }
}
