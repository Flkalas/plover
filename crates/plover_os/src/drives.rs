use crate::plfs::{Plfs, PlfsError};
use crate::vfdd::VfddDriver;
use plover_copro::vfdd::{VfdConfig, VirtualFdd};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

const SECTOR_COUNT: usize = 64;

#[derive(Debug)]
pub enum DriveError {
    BadLetter,
    AlreadyMounted,
    NotMounted,
    CannotUnmountCurrent,
    BadPath,
    Io(std::io::Error),
    Plfs(PlfsError),
    BadDosPath,
}

impl From<PlfsError> for DriveError {
    fn from(e: PlfsError) -> Self {
        DriveError::Plfs(e)
    }
}

struct MountedVolume {
    fs: Plfs,
    img_path: PathBuf,
    drive_id: u8,
}

pub struct DriveMgr {
    volumes: BTreeMap<char, MountedVolume>,
    current: char,
    next_id: u8,
}

impl DriveMgr {
    pub fn new() -> Self {
        Self {
            volumes: BTreeMap::new(),
            current: 'A',
            next_id: 0,
        }
    }

    pub fn prompt(&self) -> String {
        format!("{}>", self.current)
    }

    pub fn current_letter(&self) -> char {
        self.current
    }

    pub fn current_fs(&self) -> Result<&Plfs, DriveError> {
        self.fs_for(Some(self.current))
    }

    pub fn current_fs_mut(&mut self) -> Result<&mut Plfs, DriveError> {
        let letter = self.current;
        self.fs_for_mut(Some(letter))
    }

    pub fn fs_for(&self, letter: Option<char>) -> Result<&Plfs, DriveError> {
        let letter = letter.unwrap_or(self.current);
        self.volumes
            .get(&letter)
            .map(|v| &v.fs)
            .ok_or(DriveError::NotMounted)
    }

    pub fn fs_for_mut(&mut self, letter: Option<char>) -> Result<&mut Plfs, DriveError> {
        let letter = letter.unwrap_or(self.current);
        self.volumes
            .get_mut(&letter)
            .map(|v| &mut v.fs)
            .ok_or(DriveError::NotMounted)
    }

    pub fn drive_id(&self, letter: char) -> Option<u8> {
        self.volumes.get(&letter).map(|v| v.drive_id)
    }

    pub fn letter_for_id(&self, id: u8) -> Option<char> {
        self.volumes
            .iter()
            .find(|(_, v)| v.drive_id == id)
            .map(|(ch, _)| *ch)
    }

    pub fn mounted_letters(&self) -> Vec<char> {
        self.volumes.keys().copied().collect()
    }

    pub fn img_path(&self, letter: char) -> Option<&Path> {
        self.volumes.get(&letter).map(|v| v.img_path.as_path())
    }

    pub fn mount(&mut self, letter: char, img_path: PathBuf) -> Result<u8, DriveError> {
        let letter = normalize_letter(letter)?;
        if self.volumes.contains_key(&letter) {
            return Err(DriveError::AlreadyMounted);
        }
        if let Some(parent) = img_path.parent() {
            std::fs::create_dir_all(parent).map_err(DriveError::Io)?;
        }
        let dev = VirtualFdd::new(VfdConfig {
            path: img_path.clone(),
            sector_count: SECTOR_COUNT,
        })
        .map_err(DriveError::Io)?;
        let id = self.next_id;
        self.next_id = self.next_id.saturating_add(1);
        self.volumes.insert(
            letter,
            MountedVolume {
                fs: Plfs::new(VfddDriver::new(dev)),
                img_path,
                drive_id: id,
            },
        );
        if self.volumes.len() == 1 {
            self.current = letter;
        }
        Ok(id)
    }

    pub fn mount_formatted(
        &mut self,
        letter: char,
        img_path: PathBuf,
    ) -> Result<u8, DriveError> {
        let id = self.mount(letter, img_path)?;
        self.fs_for_mut(Some(letter))?.format()?;
        Ok(id)
    }

    pub fn unmount(&mut self, letter: char) -> Result<(), DriveError> {
        let letter = normalize_letter(letter)?;
        if letter == self.current {
            return Err(DriveError::CannotUnmountCurrent);
        }
        if self.volumes.remove(&letter).is_none() {
            return Err(DriveError::NotMounted);
        }
        Ok(())
    }

    pub fn switch(&mut self, letter: char) -> Result<(), DriveError> {
        let letter = normalize_letter(letter)?;
        if !self.volumes.contains_key(&letter) {
            return Err(DriveError::NotMounted);
        }
        self.current = letter;
        Ok(())
    }

    pub fn copy(&mut self, src: &str, dst: &str) -> Result<(), DriveError> {
        let (src_letter, src_name) = parse_dos_path(src)?;
        let (dst_letter, dst_name) = parse_dos_path(dst)?;
        if src_name.is_empty() || dst_name.is_empty() {
            return Err(DriveError::BadDosPath);
        }
        let data = self.fs_for(src_letter)?.read(src_name)?;
        let dst_fs = self.fs_for_mut(dst_letter)?;
        match dst_fs.delete(dst_name) {
            Ok(()) => {}
            Err(PlfsError::NotFound) => {}
            Err(e) => return Err(e.into()),
        }
        dst_fs.create(dst_name, &data)?;
        Ok(())
    }

    pub fn resolve_img_path(root: &Path, raw: &str) -> PathBuf {
        let p = Path::new(raw);
        if p.is_absolute() {
            return p.to_path_buf();
        }
        let direct = root.join(raw);
        if direct.is_file() {
            return direct;
        }
        root.join("hw/fixtures/vfdd").join(raw)
    }
}

impl Default for DriveMgr {
    fn default() -> Self {
        Self::new()
    }
}

fn normalize_letter(letter: char) -> Result<char, DriveError> {
    let upper = letter.to_ascii_uppercase();
    if !upper.is_ascii_uppercase() {
        return Err(DriveError::BadLetter);
    }
    Ok(upper)
}

/// Parse `B:HELLO.PLR` or `README.TXT` (current drive).
pub fn parse_dos_path(s: &str) -> Result<(Option<char>, &str), DriveError> {
    let s = s.trim();
    if s.is_empty() {
        return Err(DriveError::BadDosPath);
    }
    if let Some((head, tail)) = s.split_once(':') {
        if head.len() != 1 {
            return Err(DriveError::BadDosPath);
        }
        let letter = normalize_letter(head.chars().next().unwrap())?;
        return Ok((Some(letter), tail));
    }
    Ok((None, s))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn tmp_img(name: &str) -> PathBuf {
        let t = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("plover_drv_{name}_{t}.img"))
    }

    #[test]
    fn parse_dos_path_cases() {
        assert_eq!(parse_dos_path("B:HELLO.PLR").unwrap(), (Some('B'), "HELLO.PLR"));
        assert_eq!(parse_dos_path("README.TXT").unwrap(), (None, "README.TXT"));
        assert!(parse_dos_path("").is_err());
    }

    #[test]
    fn mount_switch_copy_unmount() {
        let a_path = tmp_img("a");
        let b_path = tmp_img("b");
        let mut mgr = DriveMgr::new();
        mgr.mount_formatted('A', a_path.clone()).unwrap();
        mgr.current_fs_mut().unwrap().create("README.TXT", b"A data").unwrap();
        mgr.mount_formatted('B', b_path.clone()).unwrap();
        mgr.switch('B').unwrap();
        assert_eq!(mgr.prompt(), "B>");
        mgr.copy("A:README.TXT", "B:README.TXT").unwrap();
        mgr.switch('A').unwrap();
        assert_eq!(mgr.current_fs_mut().unwrap().read("README.TXT").unwrap(), b"A data");
        mgr.switch('B').unwrap();
        assert_eq!(mgr.current_fs_mut().unwrap().read("README.TXT").unwrap(), b"A data");
        assert!(mgr.unmount('A').is_ok());
        assert!(mgr.unmount('B').is_err());
        let _ = std::fs::remove_file(a_path);
        let _ = std::fs::remove_file(b_path);
    }
}
