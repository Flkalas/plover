use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

pub const SECTOR_SIZE: usize = 512;

#[derive(Clone, Debug)]
pub struct VfdConfig {
    pub path: PathBuf,
    pub sector_count: usize,
}

pub struct VirtualFdd {
    cfg: VfdConfig,
}

impl VirtualFdd {
    pub fn new(cfg: VfdConfig) -> std::io::Result<Self> {
        if let Some(parent) = cfg.path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        if !cfg.path.exists() {
            std::fs::write(&cfg.path, vec![0u8; cfg.sector_count * SECTOR_SIZE])?;
        }
        Ok(Self { cfg })
    }

    pub fn read_sector(&self, n: usize) -> Result<Vec<u8>, VfddError> {
        if n >= self.cfg.sector_count {
            return Err(VfddError::SectorOutOfRange);
        }
        let mut f = std::fs::File::open(&self.cfg.path).map_err(VfddError::Io)?;
        f.seek(SeekFrom::Start((n * SECTOR_SIZE) as u64))
            .map_err(VfddError::Io)?;
        let mut buf = vec![0u8; SECTOR_SIZE];
        f.read_exact(&mut buf).map_err(|e| {
            if e.kind() == std::io::ErrorKind::UnexpectedEof {
                VfddError::ShortRead
            } else {
                VfddError::Io(e)
            }
        })?;
        Ok(buf)
    }

    pub fn write_sector(&self, n: usize, data: &[u8]) -> Result<(), VfddError> {
        if n >= self.cfg.sector_count {
            return Err(VfddError::SectorOutOfRange);
        }
        if data.len() != SECTOR_SIZE {
            return Err(VfddError::BadSectorSize);
        }
        let mut f = std::fs::OpenOptions::new()
            .read(true)
            .write(true)
            .open(&self.cfg.path)
            .map_err(VfddError::Io)?;
        f.seek(SeekFrom::Start((n * SECTOR_SIZE) as u64))
            .map_err(VfddError::Io)?;
        f.write_all(data).map_err(VfddError::Io)?;
        Ok(())
    }

    pub fn path(&self) -> &Path {
        &self.cfg.path
    }
}

#[derive(Debug)]
pub enum VfddError {
    SectorOutOfRange,
    BadSectorSize,
    ShortRead,
    Io(std::io::Error),
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn tmp_img(name: &str, _sectors: usize) -> PathBuf {
        let t = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("plover_vfdd_{name}_{t}.img"))
    }

    #[test]
    fn sector_roundtrip() {
        let path = tmp_img("rt", 8);
        let dev = VirtualFdd::new(VfdConfig {
            path: path.clone(),
            sector_count: 8,
        })
        .unwrap();
        let data = vec![0xA5u8; SECTOR_SIZE];
        dev.write_sector(3, &data).unwrap();
        assert_eq!(dev.read_sector(3).unwrap(), data);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn sector_bounds() {
        let path = tmp_img("bd", 1);
        let dev = VirtualFdd::new(VfdConfig {
            path: path.clone(),
            sector_count: 1,
        })
        .unwrap();
        assert!(matches!(
            dev.read_sector(1),
            Err(VfddError::SectorOutOfRange)
        ));
        let _ = std::fs::remove_file(path);
    }
}
