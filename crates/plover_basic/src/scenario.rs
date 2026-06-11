use crate::interpreter::{BasicVm, BasicVmError};
use crate::runtime::BasicRuntime;
use crate::tokens::{TOK_BASE, var_addr};
use plover_mmu::MemoryBus;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Debug)]
pub struct BasicScenarioResult {
    pub ok: bool,
    pub output: Vec<String>,
    pub error: Option<String>,
}

pub fn compile_bas(root: &Path, rel: &str) -> Result<Vec<u8>, String> {
    let src = root.join(rel);
    let script = root.join("basic/tokenize.py");
    let out = Command::new("python")
        .args([script.to_string_lossy().as_ref(), src.to_string_lossy().as_ref()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("python tokenize failed: {e}"))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr);
        return Err(format!("tokenize {rel}: {err}"));
    }
    Ok(out.stdout)
}

fn yaml_u64(v: &serde_yaml::Value, default: u64) -> u64 {
    match v {
        serde_yaml::Value::Number(n) => n.as_u64().or_else(|| n.as_i64().map(|i| i as u64)).unwrap_or(default),
        serde_yaml::Value::String(s) => {
            let t = s.trim();
            if let Some(hex) = t.strip_prefix("0x").or_else(|| t.strip_prefix("0X")) {
                u64::from_str_radix(hex, 16).unwrap_or(default)
            } else {
                t.parse().unwrap_or(default)
            }
        }
        _ => default,
    }
}

pub fn run_basic_scenario_yaml(
    actions: &[serde_yaml::Value],
    expect: &serde_yaml::Value,
    root: &Path,
) -> BasicScenarioResult {
    let mut bus = MemoryBus::default();
    let mut vm = BasicVm::new();
    let mut rt = BasicRuntime::new(&mut bus);
    rt.apu_init();
    rt.set_tile_color(0, 1, 0xF800);
    rt.set_tile_color(0, 3, 0x07E0);
    rt.set_tile_color(0, 4, 0xFFE0);

    for action in actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        match typ {
            "load_bas" => {
                let path = action.get("path").and_then(|v| v.as_str()).unwrap_or("");
                match compile_bas(root, path) {
                    Ok(bytes) => {
                        for (i, b) in bytes.iter().enumerate() {
                            bus.ram.write(TOK_BASE.wrapping_add(i as u16), *b);
                        }
                    }
                    Err(e) => {
                        return BasicScenarioResult {
                            ok: false,
                            output: vec![],
                            error: Some(e),
                        };
                    }
                }
            }
            "run_steps" => {
                let max = yaml_u64(
                    action
                        .get("max_steps")
                        .unwrap_or(&serde_yaml::Value::Number(500.into())),
                    500,
                ) as usize;
                for _ in 0..max {
                    match vm.step(&mut bus) {
                        Ok(()) => {}
                        Err(BasicVmError::End) => break,
                        Err(BasicVmError::UnknownOpcode(op)) => {
                            return BasicScenarioResult {
                                ok: false,
                                output: vec![],
                                error: Some(format!("unknown opcode 0x{op:02X}")),
                            };
                        }
                    }
                }
            }
            "hid_inject_key" => {
                let ch = yaml_u64(
                    action.get("char").unwrap_or(&serde_yaml::Value::Number(0.into())),
                    0,
                ) as u8;
                bus.mailbox
                    .issue_hid(plover_copro::hid::CMD_HID_INJECT, Some(&[
                        plover_copro::hid::INJECT_KEY,
                        ch,
                    ]));
            }
            other => {
                return BasicScenarioResult {
                    ok: false,
                    output: vec![],
                    error: Some(format!("unknown basic action: {other}")),
                };
            }
        }
    }

    let mut ok = true;
    let mut output = Vec::new();
    if let serde_yaml::Value::Mapping(map) = expect {
        let vdu = &bus.mailbox.vdu;
        if let Some(items) = map
            .get(&serde_yaml::Value::String("text_contains".into()))
            .and_then(|v| v.as_sequence())
        {
            let text = vdu.compose_text();
            for item in items {
                if let serde_yaml::Value::String(s) = item {
                    if !text.contains(s.as_str()) {
                        ok = false;
                        output.push(format!("missing text: {s}"));
                    }
                }
            }
        }
        if let Some(fmin) = map
            .get(&serde_yaml::Value::String("frame_min".into()))
            .and_then(|v| v.as_u64())
        {
            if u64::from(vdu.frame) < fmin {
                ok = false;
                output.push(format!("frame {} < min {fmin}", vdu.frame));
            }
        }
        if let Some(var) = map
            .get(&serde_yaml::Value::String("var".into()))
            .and_then(|v| v.as_mapping())
        {
            let name = var
                .get(&serde_yaml::Value::String("name".into()))
                .and_then(|v| v.as_str())
                .unwrap_or("X");
            let want = yaml_u64(
                var.get(&serde_yaml::Value::String("value".into()))
                    .unwrap_or(&serde_yaml::Value::Number(0.into())),
                0,
            ) as u8;
            let idx = (name.bytes().next().unwrap_or(b'X') - b'A') as usize;
            let got = bus.read_cpu(var_addr(idx));
            if got != want {
                ok = false;
                output.push(format!("var {name} = {got} != {want}"));
            }
        }
    }

    BasicScenarioResult {
        ok,
        output,
        error: None,
    }
}

pub fn repo_tokenize_script() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../basic/tokenize.py")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compile_pong_bas() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let bytes = compile_bas(&root, "hw/fixtures/basic/pong.bas").expect("tokenize");
        assert!(!bytes.is_empty());
        assert_eq!(bytes.last(), Some(&0xFF));
    }
}
