mod generic;

use plover_core::PloverMachine;
use plover_copro::apu::{CMD_APU_CH_SYNC, CMD_APU_CH_WRITE, CMD_APU_SET_CTRL, WAVE_SQUARE};
use plover_copro::hid::{CMD_HID_INJECT, CMD_HID_MOUSE_READ, INJECT_KEY, INJECT_MOUSE};
use plover_copro::vdu::{
    CMD_GFX_FILLRECT, CMD_GFX_FRAME_FLUSH, CMD_GFX_LAYER_CFG, CMD_GFX_OAM_WRITE,
    CMD_GFX_SET_TILE_PAL, CMD_GFX_TILEMAP_SET, CMD_VDU_CLS, CMD_VDU_PRINT, CMD_VDU_VSYNC,
};
use serde::Deserialize;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Debug, Deserialize)]
pub struct ScenarioDoc {
    #[serde(default)]
    pub kind: String,
    #[serde(default)]
    pub actions: Vec<serde_yaml::Value>,
    #[serde(default)]
    pub expect: serde_yaml::Value,
}

#[derive(Debug)]
pub struct ScenarioResult {
    pub ok: bool,
    pub output: Vec<String>,
    pub error: Option<String>,
}

pub fn run_scenario_file(path: &Path, root: &Path) -> ScenarioResult {
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => {
            return ScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e.to_string()),
            };
        }
    };
    let text = text.trim_start_matches('\u{FEFF}');
    let raw: serde_yaml::Value = match serde_yaml::from_str(text) {
        Ok(v) => v,
        Err(e) => {
            return ScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e.to_string()),
            };
        }
    };
    if raw.get("kind").is_none() {
        return generic::run_generic_value(&raw, root);
    }
    let doc: ScenarioDoc = match serde_yaml::from_str(text) {
        Ok(d) => d,
        Err(e) => {
            return ScenarioResult {
                ok: false,
                output: vec![],
                error: Some(e.to_string()),
            };
        }
    };
    run_scenario(&doc, root)
}

pub fn run_scenario(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    match doc.kind.as_str() {
        "vdu" => run_vdu(doc, root),
        "apu" => run_apu(doc, root),
        "hid" => run_hid(doc, root),
        "dos" => run_dos(doc, root),
        "kernel" => run_kernel(doc, root),
        "forth" => run_forth(doc),
        "basic" => run_basic(doc, root),
        other => ScenarioResult {
            ok: false,
            output: vec![],
            error: Some(format!("unknown kind: {other}")),
        },
    }
}

fn as_i64(v: &serde_yaml::Value, default: i64) -> i64 {
    match v {
        serde_yaml::Value::Number(n) => n.as_i64().unwrap_or(default),
        serde_yaml::Value::String(s) => {
            let t = s.trim();
            if let Some(hex) = t.strip_prefix("0x").or_else(|| t.strip_prefix("0X")) {
                i64::from_str_radix(hex, 16).unwrap_or(default)
            } else {
                t.parse().unwrap_or(default)
            }
        }
        _ => default,
    }
}

pub(crate) fn as_u64(v: &serde_yaml::Value, default: u64) -> u64 {
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
        serde_yaml::Value::Bool(b) => u64::from(*b),
        _ => default,
    }
}

fn yaml_get<'a>(map: &'a serde_yaml::Mapping, key: &str) -> Option<&'a serde_yaml::Value> {
    map.get(&serde_yaml::Value::String(key.into()))
}

pub fn assemble_pls(root: &Path, rel: &str, origin: u16) -> Result<Vec<u8>, String> {
    let pls = root.join(rel);
    let script = format!(
        "import sys; sys.path.insert(0, r'{}'); \
         from plover_asm.assemble import assemble_file; \
         r = assemble_file(r'{}', origin={}); \
         sys.stdout.buffer.write(bytes(r.bytes))",
        root.display(),
        pls.display(),
        origin
    );
    let out = Command::new("python")
        .args(["-c", &script])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("python assemble failed: {e}"))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr);
        return Err(format!("assemble {rel}: {err}"));
    }
    Ok(out.stdout)
}

fn apply_run_pls(m: &mut PloverMachine, action: &serde_yaml::Value, root: &Path) -> Result<(), String> {
    let path = action
        .get("path")
        .and_then(|v| v.as_str())
        .unwrap_or("hw/fixtures/sw/smoke.pls");
    let origin = as_u64(
        action
            .get("origin")
            .unwrap_or(&serde_yaml::Value::Number(0x1000.into())),
        0x1000,
    ) as u16;
    let max_steps = as_u64(
        action
            .get("max_steps")
            .unwrap_or(&serde_yaml::Value::Number(500.into())),
        500,
    ) as usize;
    let bytes = assemble_pls(root, path, origin)?;
    m.load_ram(&bytes, origin);
    m.set_pc(origin);
    m.run(max_steps);
    Ok(())
}

fn new_machine() -> PloverMachine {
    let mut m = PloverMachine::with_engine(plover_core::EngineKind::Fast);
    m.set_map_mode(1);
    m
}

fn run_vdu(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let mut m = new_machine();
    let mut out = Vec::new();

    for action in &doc.actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        let mb = &mut m.bus.mailbox;
        let res = match typ {
            "vdu_cls" => {
                let attr = as_u64(action.get("attr").unwrap_or(&serde_yaml::Value::Number(7.into())), 7) as u8;
                mb.issue_vdu(CMD_VDU_CLS, attr, 0, None);
                Ok(())
            }
            "vdu_print" => {
                let text = action.get("text").and_then(|v| v.as_str()).unwrap_or("");
                mb.issue_vdu(CMD_VDU_PRINT, text.len() as u8, 0, Some(text.as_bytes()));
                Ok(())
            }
            "gfx_fillrect" => {
                let color = as_u64(action.get("color").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u16;
                let buf = [
                    as_u64(action.get("x").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    as_u64(action.get("y").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    as_u64(action.get("w").unwrap_or(&serde_yaml::Value::Number(1.into())), 1) as u8,
                    as_u64(action.get("h").unwrap_or(&serde_yaml::Value::Number(1.into())), 1) as u8,
                    (color & 0xFF) as u8,
                    (color >> 8) as u8,
                ];
                mb.issue_vdu(CMD_GFX_FILLRECT, 0, 0, Some(&buf));
                Ok(())
            }
            "vsync" => {
                mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);
                Ok(())
            }
            "set_tile_pal" => {
                let pal = as_u64(action.get("pal").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let entry = as_u64(action.get("entry").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let color = as_u64(action.get("color").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u16;
                mb.issue_vdu(
                    CMD_GFX_SET_TILE_PAL,
                    pal,
                    entry,
                    Some(&[(color & 0xFF) as u8, (color >> 8) as u8]),
                );
                Ok(())
            }
            "layer_cfg" => {
                let layer = as_u64(action.get("layer").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let enable = as_u64(action.get("enable").unwrap_or(&serde_yaml::Value::Number(1.into())), 1) as u8;
                let sx = as_u64(action.get("scroll_x").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let sy = as_u64(action.get("scroll_y").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                mb.issue_vdu(CMD_GFX_LAYER_CFG, layer, enable, Some(&[sx, sy]));
                Ok(())
            }
            "tilemap_set" => {
                let layer = as_u64(action.get("layer").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let tx = as_u64(action.get("tile_x").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let ty = as_u64(action.get("tile_y").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let tile_id = as_u64(action.get("tile_id").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                mb.issue_vdu(CMD_GFX_TILEMAP_SET, layer, tx, Some(&[ty, tile_id]));
                Ok(())
            }
            "oam_write" => {
                let sid = as_u64(action.get("sprite_id").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let buf = [
                    as_u64(action.get("x").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    as_u64(action.get("y").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    as_u64(action.get("tile").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    as_u64(action.get("pal").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8,
                    0u8,
                    as_u64(action.get("flags").unwrap_or(&serde_yaml::Value::Number(1.into())), 1) as u8,
                ];
                mb.issue_vdu(CMD_GFX_OAM_WRITE, sid, 0, Some(&buf));
                Ok(())
            }
            "frame_flush" => {
                mb.issue_vdu(CMD_GFX_FRAME_FLUSH, 0, 0, None);
                Ok(())
            }
            "run_pls" => apply_run_pls(&mut m, action, root),
            _ => Err(format!("unknown vdu action: {typ}")),
        };
        if let Err(e) = res {
            return ScenarioResult {
                ok: false,
                output: out,
                error: Some(e),
            };
        }
    }

    let mut ok = true;
    if let serde_yaml::Value::Mapping(exp) = &doc.expect {
        let vdu = &m.bus.mailbox.vdu;
        if let Some(items) = yaml_get(exp, "text_contains").and_then(|v| v.as_sequence()) {
            let text = vdu.compose_text();
            for item in items {
                if let serde_yaml::Value::String(s) = item {
                    if !text.contains(s.as_str()) {
                        ok = false;
                        out.push(format!("missing text: {s}"));
                    }
                }
            }
        }
        if let Some(px) = yaml_get(exp, "pixel").and_then(|v| v.as_mapping()) {
            let x = yaml_get(px, "x").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
            let y = yaml_get(px, "y").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
            let want = as_u64(
                yaml_get(px, "color").unwrap_or(&serde_yaml::Value::Number(0.into())),
                0,
            ) as u16;
            let got = vdu.bitmap[y * 320 + x];
            if got != want {
                ok = false;
                out.push(format!("pixel ({x},{y}): 0x{got:04X} != 0x{want:04X}"));
            }
        }
        if let Some(f) = yaml_get(exp, "frame").and_then(|v| v.as_u64()) {
            if vdu.frame != f as u32 {
                ok = false;
                out.push(format!("frame {} != {f}", vdu.frame));
            }
        }
        if let Some(fmin) = yaml_get(exp, "frame_min").and_then(|v| v.as_u64()) {
            if u64::from(vdu.frame) < fmin {
                ok = false;
                out.push(format!("frame {} < min {fmin}", vdu.frame));
            }
        }
        if let Some(ca) = yaml_get(exp, "char_at").and_then(|v| v.as_mapping()) {
            let row = yaml_get(ca, "row").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
            let col = yaml_get(ca, "col").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
            let ch = as_u64(
                yaml_get(ca, "char").unwrap_or(&serde_yaml::Value::Number(0.into())),
                0,
            ) as u8;
            if vdu.chars[row][col] != ch {
                ok = false;
                out.push(format!("char[{row}][{col}] mismatch"));
            }
        }
    }

    ScenarioResult { ok, output: out, error: None }
}

fn run_apu(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let mut m = new_machine();
    let mut out = Vec::new();

    for action in &doc.actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        let mb = &mut m.bus.mailbox;
        let res = match typ {
            "apu_set_ctrl" => {
                let vol = as_u64(action.get("vol").unwrap_or(&serde_yaml::Value::Number(15.into())), 15) as u8;
                let mute = if action.get("mute").and_then(|v| v.as_bool()).unwrap_or(false) {
                    1
                } else {
                    0
                };
                mb.issue_apu(CMD_APU_SET_CTRL, 0, Some(&[vol, mute]));
                Ok(())
            }
            "apu_ch_write" => {
                let ch = as_u64(action.get("ch").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let period = as_u64(action.get("period").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u16;
                let vol = as_u64(action.get("vol").unwrap_or(&serde_yaml::Value::Number(15.into())), 15) as u8;
                let wave = as_u64(
                    action.get("wave").unwrap_or(&serde_yaml::Value::Number(1.into())),
                    u64::from(WAVE_SQUARE),
                ) as u8;
                mb.issue_apu(
                    CMD_APU_CH_WRITE,
                    0,
                    Some(&[ch, period as u8, (period >> 8) as u8, vol, wave]),
                );
                Ok(())
            }
            "apu_sync" => {
                mb.issue_apu(CMD_APU_CH_SYNC, 0, None);
                Ok(())
            }
            "run_pls" => apply_run_pls(&mut m, action, root),
            _ => Err(format!("unknown apu action: {typ}")),
        };
        if let Err(e) = res {
            return ScenarioResult {
                ok: false,
                output: out,
                error: Some(e),
            };
        }
    }

    let mut ok = true;
    let apu = &m.bus.mailbox.apu;
    if let serde_yaml::Value::Mapping(exp) = &doc.expect {
        if let Some(p) = yaml_get(exp, "ch0_period").and_then(|v| v.as_u64()) {
            if apu.channels[0].period != p as u16 {
                ok = false;
                out.push(format!("ch0 period {} != {p}", apu.channels[0].period));
            }
        }
        if let Some(v) = yaml_get(exp, "ch0_vol").and_then(|v| v.as_u64()) {
            if apu.channels[0].volume != v as u8 {
                ok = false;
                out.push(format!("ch0 vol {} != {v}", apu.channels[0].volume));
            }
        }
        if let Some(v) = yaml_get(exp, "master_vol").and_then(|v| v.as_u64()) {
            if apu.master_vol != v as u8 {
                ok = false;
                out.push(format!("master_vol {} != {v}", apu.master_vol));
            }
        }
        if let Some(freq) = yaml_get(exp, "mix_contains_freq").and_then(|v| v.as_f64()) {
            let n = yaml_get(exp, "mix_samples")
                .and_then(|v| v.as_u64())
                .unwrap_or(2205) as usize;
            let mut apu_mut = m.bus.mailbox.apu.clone();
            let samples = apu_mut.mix_samples(n);
            let crosses = plover_copro::apu::ApuState::zero_crossings(&samples);
            let expected = (freq * n as f64 / 22050.0 * 2.0) as usize;
            let lo = (expected as f64 * 0.7) as usize;
            let hi = (expected as f64 * 1.3) as usize + 1;
            if !(lo..=hi).contains(&crosses) {
                ok = false;
                out.push(format!("mix crossings {crosses} not in [{lo},{hi}]"));
            }
        }
    }

    ScenarioResult { ok, output: out, error: None }
}

fn run_hid(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let mut m = new_machine();
    let mut out = Vec::new();

    for action in &doc.actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        let mb = &mut m.bus.mailbox;
        let res = match typ {
            "hid_inject_key" => {
                let ch = as_u64(action.get("char").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                mb.issue_hid(CMD_HID_INJECT, Some(&[INJECT_KEY, ch]));
                Ok(())
            }
            "hid_inject_mouse" => {
                let buttons = as_u64(action.get("buttons").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let dx = as_i64(action.get("dx").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                let dy = as_i64(action.get("dy").unwrap_or(&serde_yaml::Value::Number(0.into())), 0) as u8;
                mb.issue_hid(CMD_HID_INJECT, Some(&[INJECT_MOUSE, buttons, dx, dy]));
                Ok(())
            }
            "hid_read_mouse" => {
                mb.issue_hid(CMD_HID_MOUSE_READ, None);
                Ok(())
            }
            "run_pls" => apply_run_pls(&mut m, action, root),
            _ => Err(format!("unknown hid action: {typ}")),
        };
        if let Err(e) = res {
            return ScenarioResult {
                ok: false,
                output: out,
                error: Some(e),
            };
        }
    }

    let mut ok = true;
    let hid = &m.bus.mailbox.hid;
    if let serde_yaml::Value::Mapping(exp) = &doc.expect {
        if let Some(want) = yaml_get(exp, "key_queue").and_then(|v| v.as_u64()) {
            if hid.key_queue_len() as u64 != want {
                ok = false;
                out.push(format!("key_queue {} != {want}", hid.key_queue_len()));
            }
        }
        if let Some(want) = yaml_get(exp, "last_key").and_then(|v| v.as_u64()) {
            if u64::from(hid.last_key) != want {
                ok = false;
                out.push(format!("last_key 0x{:02X} != 0x{want:02X}", hid.last_key));
            }
        }
        if let Some(want) = yaml_get(exp, "key_pending").and_then(|v| v.as_bool()) {
            if hid.key_pending() != want {
                ok = false;
                out.push(format!("key_pending {} != {want}", hid.key_pending()));
            }
        }
        if let Some(me) = yaml_get(exp, "mouse_event").and_then(|v| v.as_mapping()) {
            let want_b = yaml_get(me, "buttons").and_then(|v| v.as_u64()).unwrap_or(0) as u8;
            let want_dx = yaml_get(me, "dx").and_then(|v| v.as_i64()).unwrap_or(0) as i8;
            let want_dy = yaml_get(me, "dy").and_then(|v| v.as_i64()).unwrap_or(0) as i8;
            let ev = hid.last_mouse;
            if ev.buttons != want_b || ev.dx != want_dx || ev.dy != want_dy {
                ok = false;
                out.push(format!(
                    "mouse ({},{},{}) != ({want_b},{want_dx},{want_dy})",
                    ev.buttons, ev.dx, ev.dy
                ));
            }
        }
    }

    ScenarioResult { ok, output: out, error: None }
}

fn run_kernel(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let res = plover_os::run_kernel_scenario_yaml(&doc.actions, &doc.expect, root);
    ScenarioResult {
        ok: res.ok,
        output: res.output,
        error: res.error,
    }
}

fn run_forth(doc: &ScenarioDoc) -> ScenarioResult {
    let res = plover_forth::run_forth_scenario_yaml(&doc.actions, &doc.expect);
    ScenarioResult {
        ok: res.ok,
        output: res.output,
        error: res.error,
    }
}

fn run_basic(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let res = plover_basic::run_basic_scenario_yaml(&doc.actions, &doc.expect, root);
    ScenarioResult {
        ok: res.ok,
        output: res.output,
        error: res.error,
    }
}

fn run_dos(doc: &ScenarioDoc, root: &Path) -> ScenarioResult {
    let res = plover_os::run_dos_scenario_yaml(&doc.actions, &doc.expect, root);
    ScenarioResult {
        ok: res.ok,
        output: res.output,
        error: res.error,
    }
}

pub fn repo_root_from_manifest() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run_yaml(name: &str) -> ScenarioResult {
        let root = repo_root_from_manifest();
        run_scenario_file(&root.join("hw/scenarios/vm").join(name), &root)
    }

    #[test]
    fn vdu_smoke_yaml() {
        let res = run_yaml("vdu_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn apu_smoke_yaml() {
        let res = run_yaml("apu_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn hid_smoke_yaml() {
        let res = run_yaml("hid_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn dos_boot_yaml() {
        let res = run_yaml("dos_boot.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn add_imm_yaml() {
        let res = run_yaml("add_imm.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn boot_run_yaml() {
        let res = run_yaml("boot_run.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn boot_jmp_handoff_yaml() {
        let res = run_yaml("boot_jmp_handoff.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn forth_boot_yaml() {
        let res = run_yaml("forth_boot.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn basic_boot_yaml() {
        let res = run_yaml("basic_boot.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn rt_lib_smoke_yaml() {
        let res = run_yaml("rt_lib_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn sprite_layer_smoke_yaml() {
        let res = run_yaml("sprite_layer_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }

    #[test]
    fn rom_gpio_smoke_yaml() {
        let res = run_yaml("rom_gpio_smoke.yaml");
        assert!(res.error.is_none(), "{:?}", res.error);
        assert!(res.ok, "{:?}", res.output);
    }
}
