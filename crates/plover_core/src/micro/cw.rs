#[derive(Clone, Copy, Debug)]
pub struct ControlWord {
    pub raw: u8,
}

impl ControlWord {
    pub fn alu_op(self) -> u8 {
        (self.raw >> 4) & 0xF
    }

    pub fn reg_we(self) -> bool {
        (self.raw >> 3) & 1 != 0
    }

    pub fn y_oe(self) -> bool {
        (self.raw >> 2) & 1 != 0
    }

    pub fn mem_rd(self) -> bool {
        (self.raw >> 1) & 1 != 0
    }

    pub fn mem_wr(self) -> bool {
        self.raw & 1 != 0
    }
}

pub fn cs_index(opcode: u8, phase: u8) -> usize {
    ((opcode & 0xF) as usize) << 2 | (phase & 3) as usize
}

pub fn lookup_cw(mut nor_read: impl FnMut(usize) -> u8, opcode: u8, phase: u8) -> ControlWord {
    let idx = cs_index(opcode, phase);
    ControlWord {
        raw: nor_read(idx),
    }
}
