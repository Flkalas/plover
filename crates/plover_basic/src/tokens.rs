//! Token opcodes for host-compiled BASIC programs loaded at `TOK_BASE`.

pub const TOK_BASE: u16 = 0x2800;
pub const VAR_BASE: u16 = 0x0E10;
pub const VAR_COUNT: usize = 26;

pub const TOK_END: u8 = 0xFF;
pub const TOK_CLS: u8 = 0x87;
pub const TOK_PRINT_STR: u8 = 0x83;
pub const TOK_LET_IMM: u8 = 0x84;
pub const TOK_GOTO: u8 = 0x85;
pub const TOK_INKEY_VAR: u8 = 0x88;
pub const TOK_IF_KEY_NEQ: u8 = 0x89;
pub const TOK_ADD_VAR_IMM: u8 = 0x8A;
pub const TOK_SPRITE_VAR: u8 = 0xA1;
pub const TOK_DRAW: u8 = 0xA2;
pub const TOK_SOUND: u8 = 0xA3;
pub const TOK_LAYER_SCROLL: u8 = 0xA4;
pub const TOK_TILE: u8 = 0xA5;

pub fn var_index(name: u8) -> Option<usize> {
    let c = name.to_ascii_uppercase();
    if (b'A'..=b'Z').contains(&c) {
        Some((c - b'A') as usize)
    } else {
        None
    }
}

pub fn var_addr(idx: usize) -> u16 {
    VAR_BASE + idx as u16
}
