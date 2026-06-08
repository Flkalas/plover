pub const OP_ADD: u8 = 0x01;
pub const OP_LDA: u8 = 0x02;
pub const OP_STA: u8 = 0x03;
pub const OP_BEQ: u8 = 0x04;
pub const OP_JMP: u8 = 0x05;
pub const OP_CALL: u8 = 0x06;
pub const OP_RET: u8 = 0x07;
pub const OP_LDIO: u8 = 0x08;
pub const OP_STIO: u8 = 0x09;
pub const OP_HALT: u8 = 0x0A;
pub const OP_ADD_RR: u8 = 0x0B;
pub const OP_MOV: u8 = 0x0C;
pub const OP_CMP: u8 = 0x0D;
pub const OP_BCS: u8 = 0x0E;
pub const OP_STA16: u8 = 0x0F;
pub const OP_WADD_RR: u8 = 0x10;
pub const OP_WMOV: u8 = 0x11;
pub const OP_WCMP16: u8 = 0x12;

pub const WIDE_IMM16_OPS: [u8; 1] = [OP_WCMP16];
pub const WIDE_ABS16_OPS: [u8; 4] = [OP_BEQ, OP_JMP, OP_CALL, OP_STA16];

pub fn is_wide_imm16(op: u8) -> bool {
    WIDE_IMM16_OPS.contains(&op)
}

pub fn is_wide_abs16(op: u8) -> bool {
    WIDE_ABS16_OPS.contains(&op)
}

pub fn phase_count(opcode: u8) -> usize {
    match opcode {
        OP_ADD => 3,
        OP_LDA | OP_STA | OP_BEQ | OP_LDIO | OP_STIO | OP_STA16 => 2,
        OP_CMP => 3,
        OP_JMP | OP_CALL | OP_RET | OP_HALT | OP_MOV => 1,
        _ => 1,
    }
}
