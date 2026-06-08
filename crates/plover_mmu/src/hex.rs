use std::path::Path;

/// Load one hex byte per line into a buffer (Python `load_hex` parity).
pub fn load_hex(path: &Path, offset: usize) -> Vec<u8> {
    let mut data = Vec::new();
    let text = std::fs::read_to_string(path).unwrap_or_default();
    for (i, line) in text.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with(';') {
            continue;
        }
        let addr = offset + i;
        let val = u8::from_str_radix(line, 16).unwrap_or(0);
        if data.len() < addr + 1 {
            data.resize(addr + 1, 0);
        }
        data[addr] = val;
    }
    data
}

pub fn load_sram_program(path: &Path) -> Vec<u8> {
    load_hex(path, 0)
}
