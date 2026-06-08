use plover_core::{EngineKind, PloverMachine};
use plover_mmu::{hex::load_hex, simulate_sector_load};
use serde::Deserialize;
use std::path::Path;

use crate::{as_u64, ScenarioResult};

#[derive(Debug, Deserialize)]
struct GenericDoc {
    #[serde(default)]
    engine: String,
    #[serde(default)]
    map_mode: u64,
    #[serde(default)]
    program_base: u64,
    #[serde(default)]
    load: Option<serde_yaml::Mapping>,
    #[serde(default)]
    ram_init: Vec<serde_yaml::Value>,
    #[serde(default)]
    init: serde_yaml::Value,
    #[serde(default)]
    actions: Vec<serde_yaml::Value>,
    #[serde(default)]
    expect: serde_yaml::Value,
}

pub fn run_generic_value(raw: &serde_yaml::Value, root: &Path) -> ScenarioResult {
    let doc: GenericDoc = match serde_yaml::from_value(raw.clone()) {
        Ok(d) => d,
        Err(e) => {
            return ScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e.to_string()),
            };
        }
    };
    run_generic(&doc, root)
}

fn run_generic(doc: &GenericDoc, root: &Path) -> ScenarioResult {
    let engine = if doc.engine.is_empty() {
        EngineKind::Fast
    } else {
        EngineKind::parse(&doc.engine)
    };
    let mut m = PloverMachine::with_engine(engine);
    let mut out = Vec::new();

    if let Some(load) = &doc.load {
    for (key, val) in load {
        let key_s = key.as_str().unwrap_or("");
        let rel = val.as_str().unwrap_or("");
        let path = root.join(rel.replace('/', std::path::MAIN_SEPARATOR_STR));
        match key_s {
            "nor" => {
                m.load_nor(&path, 0);
                let vec = root.join("hw/fixtures/boot/boot_vector.hex");
                if vec.is_file() {
                    m.load_nor(&vec, 0xFFFC);
                }
                m.sync_buses();
            }
            "cw" => m.load_cw(&path),
            "program" => {
                let base = doc.program_base as u16;
                m.load_ram_program(&path, base);
            }
            _ => {}
        }
    }
    }

    for item in &doc.ram_init {
        let addr = as_u64(item.get("addr").unwrap_or(&serde_yaml::Value::Null), 0) as u16;
        if let Some(bytes) = item.get("bytes").and_then(|v| v.as_sequence()) {
            for (i, b) in bytes.iter().enumerate() {
                let v = as_u64(b, 0) as u8;
                m.bus.ram.write(addr.wrapping_add(i as u16), v);
        }
    }
    }
    m.sync_buses();

    m.set_map_mode(doc.map_mode as u8);

    let init_regs = doc
        .init
        .get("regs")
        .and_then(|v| v.as_sequence())
        .map(|seq| {
            let mut r = [0u8; 4];
            for (i, item) in seq.iter().take(4).enumerate() {
                r[i] = as_u64(item, 0) as u8;
            }
            r
        });
    let init_pc = doc
        .init
        .get("pc")
        .map(|v| as_u64(v, 0) as u16);

    if let Some(r) = init_regs {
        m.set_regs(r);
    }
    if let Some(pc) = init_pc {
        m.set_pc(pc);
    }

    for action in &doc.actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        match typ {
            "reset" => {
                let mm = action
                    .get("map_mode")
                    .map(|v| as_u64(v, m.bus.map_mode as u64) as u8)
                    .unwrap_or(m.bus.map_mode);
                m.reset(Some(mm));
                if let Some(r) = init_regs {
                    m.set_regs(r);
                }
                if let Some(pc) = init_pc {
                    m.set_pc(pc);
                }
            }
            "set_map" => {
                let mode = action
                    .get("mode")
                    .map(|v| as_u64(v, 0) as u8)
                    .unwrap_or(0);
                m.set_map_mode(mode);
            }
            "boot_sector_load" => {
                let img_rel = action
                    .get("image")
                    .and_then(|v| v.as_str())
                    .unwrap_or("hw/fixtures/vfdd/dos_boot.img");
                let path = root.join(img_rel.replace('/', std::path::MAIN_SEPARATOR_STR));
                let data = if path.extension().and_then(|s| s.to_str()) == Some("hex") {
                    load_hex(&path, 0)
                } else if path.is_file() {
                    std::fs::read(&path).unwrap_or_default()
                } else {
                    let fill = action
                        .get("fill")
                        .map(|v| as_u64(v, 0) as u8)
                        .unwrap_or(0);
                    vec![fill; 512]
                };
                simulate_sector_load(&mut m.bus, &data, 0);
            }
            "run" => {
                let steps = action
                    .get("max_steps")
                    .map(|v| as_u64(v, 10_000) as usize)
                    .unwrap_or(10_000);
                m.run(steps);
            }
            other => {
                return ScenarioResult {
                    ok: false,
                    output: out,
                    error: Some(format!("unknown generic action: {other}")),
                };
            }
        }
    }

    let snap = m.snapshot();
    let mut ok = true;
    if let serde_yaml::Value::Mapping(exp) = &doc.expect {
        if let Some(pc) = exp.get(&serde_yaml::Value::String("pc".into())) {
            let want = as_u64(pc, 0) as u16;
            if snap.pc != want {
                ok = false;
                out.push(format!("FAIL pc: {} != {want}", snap.pc));
            }
        }
        if let Some(h) = exp.get(&serde_yaml::Value::String("halted".into())) {
            let want = h.as_bool().unwrap_or(false);
            if snap.halted != want {
                ok = false;
                out.push(format!("FAIL halted: {} != {want}", snap.halted));
            }
        }
        if let Some(mm) = exp.get(&serde_yaml::Value::String("map_mode".into())) {
            let want = as_u64(mm, 0) as u8;
            if snap.map_mode != want {
                ok = false;
                out.push(format!("FAIL map_mode: {} != {want}", snap.map_mode));
            }
        }
        if let Some(fz) = exp.get(&serde_yaml::Value::String("flag_z".into())) {
            let want = fz.as_bool().unwrap_or(false);
            if snap.flag_z != want {
                ok = false;
                out.push(format!("FAIL flag_z: {} != {want}", snap.flag_z));
            }
        }
        if let Some(regs) = exp
            .get(&serde_yaml::Value::String("regs".into()))
            .and_then(|v| v.as_sequence())
        {
            for (i, item) in regs.iter().enumerate() {
                let want = as_u64(item, 0) as u8;
                if snap.regs[i] != want {
                    ok = false;
                    out.push(format!("FAIL regs[{i}]: {} != {want}", snap.regs[i]));
                }
            }
        }
        if let Some(ram) = exp
            .get(&serde_yaml::Value::String("ram".into()))
            .and_then(|v| v.as_sequence())
        {
            for item in ram {
                let addr = as_u64(item.get("addr").unwrap_or(&serde_yaml::Value::Null), 0) as u16;
                if let Some(bytes) = item.get("bytes").and_then(|v| v.as_sequence()) {
                    for (i, b) in bytes.iter().enumerate() {
                        let want = as_u64(b, 0) as u8;
                        let got = m.bus.ram.read(addr.wrapping_add(i as u16));
                        if got != want {
                            ok = false;
                            out.push(format!(
                                "FAIL ram[0x{:04X}]: 0x{got:02X} != 0x{want:02X}",
                                addr + i as u16
                            ));
                        }
                    }
                }
            }
        }
    }

    ScenarioResult {
        ok,
        output: out,
        error: None,
    }
}
