pub const MAGIC: &[u8; 4] = b"PLR\x00";
pub const HEADER_SIZE: usize = 10;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PlrImage {
    pub load_addr: u16,
    pub entry_off: u16,
    pub code: Vec<u8>,
}

impl PlrImage {
    pub fn entry_addr(&self) -> u16 {
        self.load_addr.wrapping_add(self.entry_off)
    }
}

pub fn pack_plr(img: &PlrImage) -> Vec<u8> {
    let size = (img.code.len() & 0xFFFF) as u16;
    let mut out = Vec::with_capacity(HEADER_SIZE + img.code.len());
    out.extend_from_slice(MAGIC);
    out.push((img.load_addr & 0xFF) as u8);
    out.push((img.load_addr >> 8) as u8);
    out.push((size & 0xFF) as u8);
    out.push((size >> 8) as u8);
    out.push((img.entry_off & 0xFF) as u8);
    out.push((img.entry_off >> 8) as u8);
    out.extend_from_slice(&img.code);
    out
}

#[derive(Debug)]
pub enum PlrError {
    Short,
    BadMagic,
    Truncated,
}

pub fn unpack_plr(data: &[u8]) -> Result<PlrImage, PlrError> {
    if data.len() < HEADER_SIZE {
        return Err(PlrError::Short);
    }
    if &data[..4] != MAGIC {
        return Err(PlrError::BadMagic);
    }
    let load = u16::from(data[4]) | (u16::from(data[5]) << 8);
    let size = u16::from(data[6]) | (u16::from(data[7]) << 8);
    let entry = u16::from(data[8]) | (u16::from(data[9]) << 8);
    let code = &data[10..];
    if code.len() != size as usize {
        return Err(PlrError::Truncated);
    }
    Ok(PlrImage {
        load_addr: load,
        entry_off: entry,
        code: code.to_vec(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        let img = PlrImage {
            load_addr: 0x2800,
            entry_off: 0,
            code: vec![1, 7, 12, 2, 10],
        };
        let packed = pack_plr(&img);
        let u = unpack_plr(&packed).unwrap();
        assert_eq!(u.load_addr, 0x2800);
        assert_eq!(u.code, img.code);
    }
}
