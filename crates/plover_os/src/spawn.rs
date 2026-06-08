use crate::plfs::Plfs;
use crate::plr::unpack_plr;
use plover_core::{EngineKind, PloverMachine};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExecResult {
    pub halted: bool,
    pub r0: u8,
}

pub fn spawn(machine: &mut PloverMachine, fs: &Plfs, name: &str) -> Result<ExecResult, SpawnError> {
    let plr = unpack_plr(&fs.read(name).map_err(|_| SpawnError::NotFound)?)
        .map_err(|_| SpawnError::BadPlr)?;
    machine.set_engine(EngineKind::Fast);
    machine.reset_exec_state();
    machine.load_ram_bytes(&plr.code, plr.load_addr);
    machine.set_map_mode(1);
    machine.set_pc(plr.entry_addr());
    machine.run(10_000);
    Ok(ExecResult {
        halted: machine.halted(),
        r0: machine.regs()[0],
    })
}

#[derive(Debug)]
pub enum SpawnError {
    NotFound,
    BadPlr,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::plfs::Plfs;
    use crate::plr::{pack_plr, PlrImage};
    use crate::vfdd::VfddDriver;
    use plover_copro::vfdd::{VfdConfig, VirtualFdd};
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn spawn_hello_fast() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let hello = std::fs::read(root.join("hw/fixtures/plr/hello.plr")).unwrap();
        let t = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("plover_spawn_{t}.img"));
        let dev = VirtualFdd::new(VfdConfig {
            path: path.clone(),
            sector_count: 64,
        })
        .unwrap();
        let mut fs = Plfs::new(VfddDriver::new(dev));
        fs.format().unwrap();
        fs.create("HELLO.PLR", &hello).unwrap();

        let mut m = PloverMachine::new();
        let out = spawn(&mut m, &fs, "HELLO.PLR").unwrap();
        assert!(out.halted);
        assert_eq!(out.r0, 7);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn pack_spawn_inline() {
        let img = PlrImage {
            load_addr: 0x2800,
            entry_off: 0,
            code: vec![0x01, 0x07, 0x0C, 0x02, 0x0A],
        };
        let t = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("plover_spawn2_{t}.img"));
        let dev = VirtualFdd::new(VfdConfig {
            path: path.clone(),
            sector_count: 64,
        })
        .unwrap();
        let mut fs = Plfs::new(VfddDriver::new(dev));
        fs.format().unwrap();
        fs.create("T.PLR", &pack_plr(&img)).unwrap();
        let mut m = PloverMachine::new();
        let out = spawn(&mut m, &fs, "T.PLR").unwrap();
        assert_eq!(out.r0, 7);
        let _ = std::fs::remove_file(path);
    }
}
