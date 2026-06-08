use std::collections::HashMap;
use std::sync::LazyLock;

static REG_SEL_TABLE: LazyLock<HashMap<(u8, u8), u8>> = LazyLock::new(|| {
    let entries = [
        (0x01, 0, 0),
        (0x01, 1, 1),
        (0x01, 2, 2),
        (0x02, 0, 0),
        (0x02, 1, 0),
        (0x03, 0, 0),
        (0x03, 1, 0),
        (0x04, 0, 0),
        (0x04, 1, 0),
        (0x05, 0, 0),
        (0x06, 0, 0),
        (0x07, 0, 0),
        (0x08, 0, 0),
        (0x08, 1, 0),
        (0x09, 0, 0),
        (0x09, 1, 0),
        (0x0A, 0, 0),
        (0x0D, 0, 0),
        (0x0D, 1, 1),
    ];
    entries
        .into_iter()
        .map(|(op, ph, sel)| ((op, ph), sel))
        .collect()
});

pub fn reg_sel(opcode: u8, phase: u8) -> u8 {
    *REG_SEL_TABLE
        .get(&(opcode & 0xF, phase & 3))
        .unwrap_or(&0)
}
