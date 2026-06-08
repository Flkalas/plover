use crate::kernel::Kernel;
use crate::plfs::Plfs;
use crate::plr::{pack_plr, PlrImage};
use crate::shell::{DosRuntime, ScenarioAction};
use crate::vfdd::VfddDriver;
use plover_core::PloverMachine;
use plover_copro::vfdd::{VfdConfig, VirtualFdd, SECTOR_SIZE};
use std::path::{Path, PathBuf};

#[derive(Debug)]
pub struct DosScenarioResult {
    pub ok: bool,
    pub output: Vec<String>,
    pub error: Option<String>,
}

pub fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

pub fn prepare_runtime(root: &Path, img_name: &str) -> Result<DosRuntime, String> {
    let img_path = root.join("hw/fixtures/vfdd").join(img_name);
    let dev = VirtualFdd::new(VfdConfig {
        path: img_path,
        sector_count: 64,
    })
    .map_err(|e| e.to_string())?;
    let mut fs = Plfs::new(VfddDriver::new(dev));
    fs.format().map_err(|e| format!("{e:?}"))?;

    let stage1 = {
        let mut s = b"PLDOS_STAGE1".to_vec();
        s.resize(SECTOR_SIZE, 0);
        s
    };
    fs.drv.write_sector(0, &stage1).map_err(|e| format!("{e:?}"))?;

    let hello = std::fs::read(root.join("hw/fixtures/plr/hello.plr"))
        .map_err(|e| format!("hello.plr: {e}"))?;
    fs.create("HELLO.PLR", &hello)
        .map_err(|e| format!("{e:?}"))?;
    fs.create("README.TXT", b"PL-DOS VM")
        .map_err(|e| format!("{e:?}"))?;

    let command = pack_plr(&PlrImage {
        load_addr: 0x3000,
        entry_off: 0,
        code: vec![0x0A],
    });
    fs.create("COMMAND.PLR", &command)
        .map_err(|e| format!("{e:?}"))?;

    let machine = PloverMachine::new();
    let kernel = Kernel::new(machine.bus.clone());

    Ok(DosRuntime {
        fs,
        machine,
        kernel,
        root: root.to_path_buf(),
        output: Vec::new(),
        prompt: "PL-DOS>".to_string(),
        last_link_map: std::collections::BTreeMap::new(),
        last_link_reloc_count: 0,
    })
}

pub fn run_dos_scenario_yaml(
    actions: &[serde_yaml::Value],
    expect: &serde_yaml::Value,
    root: &Path,
) -> DosScenarioResult {
    let parsed = match parse_dos_actions(actions) {
        Ok(a) => a,
        Err(e) => {
            return DosScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e),
            };
        }
    };
    let exp = parse_dos_expect(expect);
    run_dos_scenario(&parsed, &exp, root)
}

fn parse_dos_actions(actions: &[serde_yaml::Value]) -> Result<Vec<ScenarioAction>, String> {
    let mut out = Vec::new();
    for action in actions {
        let typ = action
            .get("type")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        match typ {
            "command" => {
                let line = action
                    .get("line")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                out.push(ScenarioAction::Command { line });
            }
            "dir" => out.push(ScenarioAction::Dir),
            "run" => {
                let name = action
                    .get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or("HELLO.PLR")
                    .to_string();
                out.push(ScenarioAction::Run { name });
            }
            other => return Err(format!("unknown dos action: {other}")),
        }
    }
    Ok(out)
}

fn parse_dos_expect(expect: &serde_yaml::Value) -> Vec<String> {
    let mut out = Vec::new();
    if let serde_yaml::Value::Mapping(map) = expect {
        if let Some(items) = map.get(&serde_yaml::Value::String("output_contains".into())) {
            if let serde_yaml::Value::Sequence(seq) = items {
                for item in seq {
                    if let serde_yaml::Value::String(s) = item {
                        out.push(s.clone());
                    }
                }
            }
        }
    }
    out
}

pub fn run_dos_scenario(actions: &[ScenarioAction], expect: &[String], root: &Path) -> DosScenarioResult {
    let mut rt = match prepare_runtime(root, "dos_boot.img") {
        Ok(r) => r,
        Err(e) => {
            return DosScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e),
            };
        }
    };
    rt.stage1_boot();
    rt.stage2_shell_start();
    for action in actions {
        match action {
            ScenarioAction::Command { line } => {
                rt.run_command(line);
            }
            ScenarioAction::Dir => {
                rt.run_command("dir");
            }
            ScenarioAction::Run { name } => {
                rt.run_command(&format!("run {name}"));
            }
        }
    }
    let ok = expect.iter().all(|s| rt.output.iter().any(|line| line.contains(s)));
    DosScenarioResult {
        ok,
        output: rt.output,
        error: None,
    }
}
