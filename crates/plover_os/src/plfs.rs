use crate::vfdd::VfddDriver;
use plover_copro::SECTOR_SIZE;

pub const DIR_SECTOR: usize = 1;
pub const DATA_BASE: usize = 2;
pub const ENTRY_SIZE: usize = 16;
pub const ENTRIES_PER_SECTOR: usize = SECTOR_SIZE / ENTRY_SIZE;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DirEntry {
    pub name11: [u8; 11],
    pub start_sector: u16,
    pub size_bytes: u16,
    pub attr: u8,
}

fn norm_name(name: &str) -> [u8; 11] {
    let upper = name.to_ascii_uppercase();
    let (a, b) = match upper.split_once('.') {
        Some((x, y)) => (x, y),
        None => (upper.as_str(), ""),
    };
    let mut out = [b' '; 11];
    for (i, c) in a.chars().take(8).enumerate() {
        out[i] = c as u8;
    }
    for (i, c) in b.chars().take(3).enumerate() {
        out[8 + i] = c as u8;
    }
    out
}

impl DirEntry {
    fn pack(&self) -> [u8; ENTRY_SIZE] {
        let mut buf = [0u8; ENTRY_SIZE];
        buf[..11].copy_from_slice(&self.name11);
        buf[11] = (self.start_sector & 0xFF) as u8;
        buf[12] = (self.start_sector >> 8) as u8;
        buf[13] = (self.size_bytes & 0xFF) as u8;
        buf[14] = (self.size_bytes >> 8) as u8;
        buf[15] = self.attr;
        buf
    }

    fn unpack(data: &[u8]) -> Option<Self> {
        if data.len() != ENTRY_SIZE {
            return None;
        }
        let mut name11 = [0u8; 11];
        name11.copy_from_slice(&data[..11]);
        if name11 == [0u8; 11] || name11 == [b' '; 11] {
            return None;
        }
        let start = u16::from(data[11]) | (u16::from(data[12]) << 8);
        let size = u16::from(data[13]) | (u16::from(data[14]) << 8);
        Some(DirEntry {
            name11,
            start_sector: start,
            size_bytes: size,
            attr: data[15],
        })
    }
}

pub struct Plfs {
    pub drv: VfddDriver,
}

#[derive(Debug)]
pub enum PlfsError {
    Exists,
    NotFound,
    DirFull,
    Vfdd(plover_copro::vfdd::VfddError),
}

impl From<plover_copro::vfdd::VfddError> for PlfsError {
    fn from(e: plover_copro::vfdd::VfddError) -> Self {
        PlfsError::Vfdd(e)
    }
}

impl Plfs {
    pub fn new(drv: VfddDriver) -> Self {
        Self { drv }
    }

    pub fn format(&mut self) -> Result<(), PlfsError> {
        self.drv
            .write_sector(DIR_SECTOR, &vec![0u8; SECTOR_SIZE])?;
        Ok(())
    }

    fn load_dir(&self) -> Result<Vec<Option<DirEntry>>, PlfsError> {
        let sec = self.drv.read_sector(DIR_SECTOR)?;
        let mut out = Vec::with_capacity(ENTRIES_PER_SECTOR);
        for i in 0..ENTRIES_PER_SECTOR {
            let chunk = &sec[i * ENTRY_SIZE..(i + 1) * ENTRY_SIZE];
            out.push(DirEntry::unpack(chunk));
        }
        Ok(out)
    }

    fn store_dir(&self, entries: &[Option<DirEntry>]) -> Result<(), PlfsError> {
        let mut buf = vec![0u8; SECTOR_SIZE];
        for (i, e) in entries.iter().take(ENTRIES_PER_SECTOR).enumerate() {
            if let Some(ent) = e {
                buf[i * ENTRY_SIZE..(i + 1) * ENTRY_SIZE].copy_from_slice(&ent.pack());
            }
        }
        self.drv.write_sector(DIR_SECTOR, &buf)?;
        Ok(())
    }

    pub fn list(&self) -> Result<Vec<DirEntry>, PlfsError> {
        Ok(self
            .load_dir()?
            .into_iter()
            .flatten()
            .collect())
    }

    fn find(&self, name: &str) -> Result<Option<(usize, DirEntry)>, PlfsError> {
        let want = norm_name(name);
        for (i, e) in self.load_dir()?.into_iter().enumerate() {
            if let Some(ent) = e {
                if ent.name11 == want {
                    return Ok(Some((i, ent)));
                }
            }
        }
        Ok(None)
    }

    pub fn create(&mut self, name: &str, data: &[u8]) -> Result<(), PlfsError> {
        if self.find(name)?.is_some() {
            return Err(PlfsError::Exists);
        }
        let mut entries = self.load_dir()?;
        let slot = entries
            .iter()
            .position(|e| e.is_none())
            .ok_or(PlfsError::DirFull)?;

        let mut used_end = DATA_BASE;
        for e in entries.iter().flatten() {
            let end = e.start_sector as usize
                + ((e.size_bytes as usize + SECTOR_SIZE - 1) / SECTOR_SIZE);
            used_end = used_end.max(end);
        }
        let start = used_end;
        let nsectors = (data.len() + SECTOR_SIZE - 1) / SECTOR_SIZE;
        for s in 0..nsectors {
            let off = s * SECTOR_SIZE;
            let mut chunk = vec![0u8; SECTOR_SIZE];
            let end = (off + SECTOR_SIZE).min(data.len());
            chunk[..end - off].copy_from_slice(&data[off..end]);
            self.drv.write_sector(start + s, &chunk)?;
        }

        entries[slot] = Some(DirEntry {
            name11: norm_name(name),
            start_sector: start as u16,
            size_bytes: data.len() as u16,
            attr: 0,
        });
        self.store_dir(&entries)
    }

    pub fn read(&self, name: &str) -> Result<Vec<u8>, PlfsError> {
        let (_, e) = self.find(name)?.ok_or(PlfsError::NotFound)?;
        let nsectors = (e.size_bytes as usize + SECTOR_SIZE - 1) / SECTOR_SIZE;
        let mut buf = Vec::new();
        for s in 0..nsectors {
            buf.extend_from_slice(&self.drv.read_sector(e.start_sector as usize + s)?);
        }
        buf.truncate(e.size_bytes as usize);
        Ok(buf)
    }

    pub fn delete(&mut self, name: &str) -> Result<(), PlfsError> {
        let (idx, _) = self.find(name)?.ok_or(PlfsError::NotFound)?;
        let mut entries = self.load_dir()?;
        entries[idx] = None;
        self.store_dir(&entries)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use plover_copro::vfdd::{VfdConfig, VirtualFdd};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn tmp_disk() -> (std::path::PathBuf, Plfs) {
        let t = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("plover_plfs_{t}.img"));
        let dev = VirtualFdd::new(VfdConfig {
            path: path.clone(),
            sector_count: 64,
        })
        .unwrap();
        let mut fs = Plfs::new(VfddDriver::new(dev));
        fs.format().unwrap();
        (path, fs)
    }

    #[test]
    fn create_read_delete() {
        let (path, mut fs) = tmp_disk();
        fs.create("HELLO.TXT", b"hello").unwrap();
        assert_eq!(fs.read("HELLO.TXT").unwrap(), b"hello");
        assert_eq!(fs.list().unwrap()[0].name11, *b"HELLO   TXT");
        fs.delete("HELLO.TXT").unwrap();
        assert!(fs.list().unwrap().is_empty());
        let _ = std::fs::remove_file(path);
    }
}
