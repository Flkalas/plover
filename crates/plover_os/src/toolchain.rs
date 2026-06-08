use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

pub fn assemble_pls_to_plr(root: &Path, pls_rel: &str, origin: u16) -> Result<Vec<u8>, String> {
    let pls = root.join(pls_rel.replace('/', std::path::MAIN_SEPARATOR_STR));
    let script = format!(
        "import sys; sys.path.insert(0, r'{}'); \
         from plover_asm.assemble import assemble_file; \
         from kern.plr import pack_plr, PlrImage; \
         r = assemble_file(r'{}', origin={}); \
         sys.stdout.buffer.write(pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(r.bytes))))",
        root.display(),
        pls.display(),
        origin
    );
    run_python_bytes(&script)
}

pub fn ccrun_to_plr(root: &Path, c_rel: &str) -> Result<Vec<u8>, String> {
    let c_path = root.join(c_rel.replace('/', std::path::MAIN_SEPARATOR_STR));
    let script = format!(
        "import sys; sys.path.insert(0, r'{}'); \
         from plover_cc.parse import parse as cc_parse; \
         from plover_cc.codegen import program_to_asm; \
         from plover_asm.assemble import assemble; \
         from kern.plr import pack_plr, PlrImage; \
         text = open(r'{}', encoding='utf-8').read(); \
         prog = cc_parse(text); \
         asm = program_to_asm(prog); \
         r = assemble(asm, origin=0); \
         sys.stdout.buffer.write(pack_plr(PlrImage(load_addr=0x2800, entry_off=0, code=bytes(r.bytes))))",
        root.display(),
        c_path.display()
    );
    run_python_bytes(&script)
}

pub struct LinkResult {
    pub plr: Vec<u8>,
    pub symbols: BTreeMap<String, u16>,
    pub reloc_applied: u16,
    pub entry_symbol: String,
}

pub fn link_plx_to_plr(root: &Path, plx_paths: &[PathBuf]) -> Result<LinkResult, String> {
    let paths_py: String = plx_paths
        .iter()
        .map(|p| format!("r'{}'", p.display()))
        .collect::<Vec<_>>()
        .join(", ");
    let script = format!(
        "import sys; sys.path.insert(0, r'{}'); \
         from plover_ld.format import read_plx; \
         from plover_ld.linker import link_objects; \
         from kern.plr import pack_plr, PlrImage; \
         import json; \
         paths = [{}]; \
         objs = [read_plx(p) for p in paths]; \
         lr = link_objects(objs, text_base=0x2800); \
         entry_addr = lr.symbols.get(lr.entry_symbol, 0x2800); \
         plr = pack_plr(PlrImage(load_addr=0x2800, entry_off=(entry_addr - 0x2800) & 0xFFFF, code=lr.final_code())); \
         sys.stdout.buffer.write(plr); \
         meta = json.dumps({{'symbols': lr.symbols, 'reloc': lr.reloc_applied, 'entry': lr.entry_symbol}}); \
         sys.stderr.write(meta)",
        root.display(),
        paths_py
    );
    let out = Command::new("python")
        .args(["-c", &script])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("python: {e}"))?;
    if !out.status.success() {
        return Err(String::from_utf8_lossy(&out.stderr).into_owned());
    }
    let meta: serde_json::Value =
        serde_json::from_str(std::str::from_utf8(&out.stderr).unwrap_or("{}")).unwrap_or_default();
    let symbols: BTreeMap<String, u16> = meta
        .get("symbols")
        .and_then(|v| v.as_object())
        .map(|m| {
            m.iter()
                .filter_map(|(k, v)| v.as_u64().map(|u| (k.clone(), u as u16)))
                .collect()
        })
        .unwrap_or_default();
    let reloc = meta
        .get("reloc")
        .and_then(|v| v.as_u64())
        .unwrap_or(0) as u16;
    let entry = meta
        .get("entry")
        .and_then(|v| v.as_str())
        .unwrap_or("_start")
        .to_string();
    Ok(LinkResult {
        plr: out.stdout,
        symbols,
        reloc_applied: reloc,
        entry_symbol: entry,
    })
}

fn run_python_bytes(script: &str) -> Result<Vec<u8>, String> {
    let out = Command::new("python")
        .args(["-c", script])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("python: {e}"))?;
    if !out.status.success() {
        return Err(String::from_utf8_lossy(&out.stderr).into_owned());
    }
    Ok(out.stdout)
}
