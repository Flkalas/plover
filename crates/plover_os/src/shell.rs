use crate::kernel::Kernel;
use crate::plfs::Plfs;
use crate::spawn::spawn;
use crate::toolchain::{assemble_pls_to_plr, ccrun_to_plr, link_plx_to_plr};
use plover_core::PloverMachine;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

pub enum ScenarioAction {
    Command { line: String },
    Dir,
    Run { name: String },
}

pub struct DosRuntime {
    pub fs: Plfs,
    pub machine: PloverMachine,
    pub kernel: Kernel,
    pub root: PathBuf,
    pub output: Vec<String>,
    pub prompt: String,
    pub last_link_map: BTreeMap<String, u16>,
    pub last_link_reloc_count: u16,
}

impl DosRuntime {
    fn emit(&mut self, s: &str, acc: &mut Vec<String>) {
        let line = if s.len() > 40 { &s[..40] } else { s };
        self.output.push(line.to_string());
        acc.push(line.to_string());
    }

    pub fn stage1_boot(&mut self) {
        let mut out = Vec::new();
        self.kernel.boot();
        self.emit("stage1_kernel_ready", &mut out);
    }

    pub fn stage2_shell_start(&mut self) {
        let mut out = Vec::new();
        self.emit("stage2_shell_ready", &mut out);
        let prompt = self.prompt.clone();
        self.emit(&prompt, &mut out);
    }

    fn reset_exec_state(&mut self) {
        self.machine.reset_exec_state();
    }

    fn run_plr_bytes(&mut self, plr_name: &str, plr_bytes: &[u8], out: &mut Vec<String>) {
        let _ = self.fs.delete(plr_name);
        if let Err(e) = self.fs.create(plr_name, plr_bytes) {
            self.emit(&format!("ERR fs:{e:?}"), out);
            return;
        }
        self.reset_exec_state();
        match spawn(&mut self.machine, &self.fs, plr_name) {
            Ok(r) => self.emit(&format!("R0_{}", r.r0), out),
            Err(_) => self.emit("ERR spawn", out),
        }
    }

    fn resolve_path(&self, p: &str) -> PathBuf {
        let path = Path::new(p);
        if path.is_absolute() {
            path.to_path_buf()
        } else {
            self.root.join(p)
        }
    }

    pub fn run_command(&mut self, line: &str) -> Vec<String> {
        let mut out = Vec::new();
        let parts = split_shell_line(line);
        if parts.is_empty() {
            let prompt = self.prompt.clone();
            self.emit(&prompt, &mut out);
            return out;
        }
        let cmd = parts[0].to_ascii_lowercase();
        match cmd.as_str() {
            "dir" => {
                if let Ok(entries) = self.fs.list() {
                    for e in entries {
                        let name = String::from_utf8_lossy(&e.name11)
                            .trim()
                            .to_string();
                        self.emit(&name, &mut out);
                    }
                }
            }
            "run" => {
                if parts.len() < 2 {
                    self.emit("ERR missing filename", &mut out);
                } else {
                    let target = &parts[1];
                    if target.to_ascii_lowercase().ends_with(".plx") {
                        let src = self.resolve_path(target);
                        if !src.is_file() {
                            self.emit(&format!("ERR missing file: {}", src.display()), &mut out);
                        } else if let Ok(lr) = link_plx_to_plr(&self.root, &[src]) {
                            self.last_link_map = lr.symbols;
                            self.last_link_reloc_count = lr.reloc_applied;
                            self.run_plr_bytes("RUN.PLR", &lr.plr, &mut out);
                        } else {
                            self.emit("ERR link", &mut out);
                        }
                    } else {
                        self.reset_exec_state();
                        match spawn(&mut self.machine, &self.fs, target) {
                            Ok(r) => self.emit(&format!("R0_{}", r.r0), &mut out),
                            Err(_) => self.emit("ERR spawn", &mut out),
                        }
                    }
                }
            }
            "ldrun" => {
                if parts.len() < 2 {
                    self.emit("ERR usage: ldrun <obj1.plx> [obj2.plx ...]", &mut out);
                } else {
                    let mut paths = Vec::new();
                    let mut bad = false;
                    for p in &parts[1..] {
                        let src = self.resolve_path(p);
                        if !src.is_file() {
                            self.emit(&format!("ERR missing file: {}", src.display()), &mut out);
                            bad = true;
                            break;
                        }
                        paths.push(src);
                    }
                    if !bad {
                        match link_plx_to_plr(&self.root, &paths) {
                            Ok(lr) => {
                                self.last_link_map = lr.symbols;
                                self.last_link_reloc_count = lr.reloc_applied;
                                self.run_plr_bytes("LDRUN.PLR", &lr.plr, &mut out);
                            }
                            Err(e) => self.emit(&format!("ERR link:{e}"), &mut out),
                        }
                    }
                }
            }
            "type" => {
                if parts.len() < 2 {
                    self.emit("ERR missing filename", &mut out);
                } else {
                    match self.fs.read(&parts[1]) {
                        Ok(data) => self.emit(
                            &String::from_utf8_lossy(&data).replace('\n', " "),
                            &mut out,
                        ),
                        Err(_) => self.emit("ERR not found", &mut out),
                    }
                }
            }
            "del" => {
                if parts.len() < 2 {
                    self.emit("ERR missing filename", &mut out);
                } else {
                    match self.fs.delete(&parts[1]) {
                        Ok(()) => self.emit("OK", &mut out),
                        Err(_) => self.emit("ERR not found", &mut out),
                    }
                }
            }
            "mon" => {
                self.cmd_mon(&parts[1..], &mut out);
            }
            "plsrun" => {
                if parts.len() < 2 {
                    self.emit("ERR usage: plsrun <path.pls>", &mut out);
                } else {
                    let src = self.resolve_path(&parts[1]);
                    if !src.is_file() {
                        self.emit(&format!("ERR missing file: {}", src.display()), &mut out);
                    } else {
                        let rel = src
                            .strip_prefix(&self.root)
                            .unwrap_or(src.as_path())
                            .to_string_lossy()
                            .replace('\\', "/");
                        match assemble_pls_to_plr(&self.root, &rel, 0) {
                            Ok(plr) => self.run_plr_bytes("PLSRUN.PLR", &plr, &mut out),
                            Err(e) => self.emit(&format!("ERR asm:{e}"), &mut out),
                        }
                    }
                }
            }
            "ccrun" => {
                if parts.len() < 2 {
                    self.emit("ERR usage: ccrun <path.c>", &mut out);
                } else {
                    let src = self.resolve_path(&parts[1]);
                    if !src.is_file() {
                        self.emit(&format!("ERR missing file: {}", src.display()), &mut out);
                    } else {
                        let rel = src
                            .strip_prefix(&self.root)
                            .unwrap_or(src.as_path())
                            .to_string_lossy()
                            .replace('\\', "/");
                        match ccrun_to_plr(&self.root, &rel) {
                            Ok(plr) => self.run_plr_bytes("CCRUN.PLR", &plr, &mut out),
                            Err(e) => self.emit(&format!("ERR cc:{e}"), &mut out),
                        }
                    }
                }
            }
            "help" => {
                self.emit(
                    "dir type del run ldrun plsrun ccrun mon [cpu|ram|vfdd|gpio|serial|dev|map|sym|rel|vdu] help exit",
                    &mut out,
                );
            }
            "exit" => {
                self.emit("BYE", &mut out);
                return out;
            }
            _ => {
                self.emit(&format!("ERR unknown:{}", parts[0]), &mut out);
            }
        }
        let prompt = self.prompt.clone();
        self.emit(&prompt, &mut out);
        out
    }

    fn cmd_mon(&mut self, args: &[String], out: &mut Vec<String>) {
        let sub = args.first().map(|s| s.to_ascii_lowercase()).unwrap_or_default();
        match sub.as_str() {
            "" | "cpu" => {
                let s = self.machine.snapshot();
                self.emit(
                    &format!(
                        "PC_{:04X} R0_{:02X} R1_{:02X} R2_{:02X} R3_{:02X} HALT_{}",
                        s.pc, s.regs[0], s.regs[1], s.regs[2], s.regs[3], s.halted as u8
                    ),
                    out,
                );
            }
            "ram" => {
                let nz = self.machine.ram_nonzero();
                let free = 65536usize.saturating_sub(nz);
                self.emit(&format!("RAM_USED_{nz}B RAM_FREE_{free}B"), out);
            }
            "vfdd" => {
                let entries = self.fs.list().unwrap_or_default();
                let mut used = 2usize;
                for e in &entries {
                    used += ((e.size_bytes as usize) + 511) / 512;
                }
                self.emit(
                    &format!(
                        "VFDD_FILES_{} VFDD_USED_SECT_{used} VFDD_TOTAL_SECT_64",
                        entries.len()
                    ),
                    out,
                );
            }
            "gpio" => {
                self.emit(
                    &format!("GPIO_PORTA_{:02X}", self.kernel.gpio.read_port()),
                    out,
                );
            }
            "serial" => {
                let st = self.kernel.serial.status();
                self.emit(
                    &format!(
                        "SERIAL_SIG_{:02X} STATUS_{st:02X} TXQ_{} RXQ_{}",
                        self.kernel.serial.signature,
                        self.kernel.serial.tx_fifo.len(),
                        self.kernel.serial.rx_fifo.len()
                    ),
                    out,
                );
            }
            "dev" => {
                let lines: Vec<String> = if self.kernel.state.device_table.is_empty() {
                    vec!["DEV empty".to_string()]
                } else {
                    self.kernel
                        .state
                        .device_table
                        .iter()
                        .map(|(slot, drv)| {
                            let sig = self
                                .kernel
                                .state
                                .slot_signatures
                                .get(slot)
                                .copied()
                                .unwrap_or(0xFF);
                            format!("DEV_SLOT_{slot} SIG_{sig:02X} DRV_{drv}")
                        })
                        .collect()
                };
                for line in lines {
                    self.emit(&line, out);
                }
            }
            "map" => {
                let lines: Vec<String> = if self.last_link_map.is_empty() {
                    vec!["MAP empty".to_string()]
                } else {
                    self.last_link_map
                        .iter()
                        .map(|(k, v)| format!("{k}_${v:04X}"))
                        .collect()
                };
                for line in lines {
                    self.emit(&line, out);
                }
            }
            "sym" => {
                if self.last_link_map.is_empty() {
                    self.emit("SYM empty", out);
                } else {
                    let mut keys: Vec<_> = self.last_link_map.keys().cloned().collect();
                    keys.sort();
                    self.emit(&format!("SYM {}", keys.join(" ")), out);
                }
            }
            "rel" => {
                self.emit(
                    &format!("RELOC_APPLIED_{}", self.last_link_reloc_count),
                    out,
                );
            }
            "vdu" => {
                let v = self.machine.bus.mailbox.vdu.clone();
                self.emit(
                    &format!(
                        "VDU_MODE_{} CUR_{}_{} FRAME_{}",
                        v.mode, v.cursor_col, v.cursor_row, v.frame
                    ),
                    out,
                );
                let row0: String = v.chars[0]
                    .iter()
                    .map(|&c| c as char)
                    .collect::<String>()
                    .trim_end()
                    .to_string();
                if !row0.is_empty() {
                    self.emit(&row0, out);
                }
            }
            _ => {
                self.emit(
                    "ERR usage: mon [cpu|ram|vfdd|gpio|serial|dev|map|sym|rel|vdu]",
                    out,
                );
            }
        }
    }
}

fn split_shell_line(line: &str) -> Vec<String> {
    line.trim()
        .split_whitespace()
        .map(|s| s.to_string())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::prepare_runtime;

    fn test_img(tag: &str) -> String {
        format!("test_{tag}.img")
    }

    #[test]
    fn dos_boot_flow() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut rt = prepare_runtime(&root, &test_img("dos_boot_flow")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        rt.run_command("dir");
        rt.run_command("run HELLO.PLR");
        assert!(rt.output.iter().any(|l| l.contains("HELLO")));
        assert!(rt.output.iter().any(|l| l.contains("R0_7")));
    }

    #[test]
    fn shell_monitor_and_compile_commands() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut rt = prepare_runtime(&root, &test_img("shell_monitor")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        rt.run_command("mon");
        rt.run_command("plsrun hw/fixtures/sw/add_imm.pls");
        rt.run_command("ccrun hw/fixtures/sw/cc_smoke.c");
        let out = rt.output.join("\n");
        assert!(out.contains("PC_") && out.contains("R0_"), "{out}");
        assert!(out.contains("R0_8"), "{out}");
        assert!(out.contains("R0_5"), "{out}");
    }

    #[test]
    fn ldrun_and_link_monitors() {
        use std::process::Command;

        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let build_dir = root.join("build/tmp_obj");
        std::fs::create_dir_all(&build_dir).unwrap();
        let obj = root.join("hw/fixtures/sw/add_imm.pls");
        let status = Command::new("python")
            .args([
                "-m",
                "plover_asm",
                "obj",
                obj.to_str().unwrap(),
                "-o",
                build_dir.to_str().unwrap(),
            ])
            .current_dir(&root)
            .status()
            .expect("python plover_asm");
        assert!(status.success(), "plover_asm obj failed");

        let mut rt = prepare_runtime(&root, &test_img("ldrun")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        rt.run_command("ldrun build/tmp_obj/add_imm.plx");
        rt.run_command("mon map");
        rt.run_command("mon sym");
        rt.run_command("mon rel");
        let out = rt.output.join("\n");
        assert!(out.contains("R0_8"), "{out}");
        assert!(out.contains("MAP") || out.contains("_$"), "{out}");
        assert!(out.contains("SYM"), "{out}");
        assert!(out.contains("RELOC_APPLIED_"), "{out}");
    }

    #[test]
    fn monitor_ram_vfdd_gpio_dev_serial() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut rt = prepare_runtime(&root, &test_img("monitor")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        rt.run_command("mon ram");
        rt.run_command("mon vfdd");
        rt.run_command("mon dev");
        rt.run_command("mon gpio");
        rt.run_command("mon serial");
        let out = rt.output.join("\n");
        assert!(out.contains("RAM_USED_") && out.contains("RAM_FREE_"), "{out}");
        assert!(out.contains("VFDD_FILES_") && out.contains("VFDD_USED_SECT_"), "{out}");
        assert!(out.contains("DEV_SLOT_"), "{out}");
        assert!(out.contains("GPIO_PORTA_"), "{out}");
        assert!(out.contains("SERIAL_SIG_D4"), "{out}");
    }
}
