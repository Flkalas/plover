use crate::drives::{parse_dos_path, DriveError, DriveMgr};
use crate::kernel::Kernel;
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
    pub drives: DriveMgr,
    pub machine: PloverMachine,
    pub kernel: Kernel,
    pub root: PathBuf,
    pub output: Vec<String>,
    pub last_link_map: BTreeMap<String, u16>,
    pub last_link_reloc_count: u16,
}

impl DosRuntime {
    const COLS: usize = 40;

    pub fn prompt(&self) -> String {
        self.drives.prompt()
    }

    fn emit(&mut self, s: &str, acc: &mut Vec<String>) {
        for line in wrap_console_lines(s, Self::COLS) {
            self.vdu_print_line(&line);
            self.output.push(line.clone());
            acc.push(line);
        }
    }

    fn vdu_print_line(&mut self, line: &str) {
        use plover_copro::vdu::CMD_VDU_PRINT;
        if !line.is_empty() {
            let bytes = line.as_bytes();
            let len = bytes.len().min(255) as u8;
            self.machine
                .bus
                .mailbox
                .issue_vdu(CMD_VDU_PRINT, len, 0, Some(bytes));
        }
        let col = self.machine.bus.mailbox.vdu.cursor_col;
        // A full 40-column line already auto-wrapped; avoid a second newline.
        if line.len() >= Self::COLS && col == 0 {
            return;
        }
        self.vdu_putch(b'\n');
    }

    fn vdu_vsync(&mut self) {
        use plover_copro::vdu::CMD_VDU_VSYNC;
        self.machine
            .bus
            .mailbox
            .issue_vdu(CMD_VDU_VSYNC, 0, 0, None);
    }

    pub fn vdu_putch(&mut self, ch: u8) {
        use plover_copro::vdu::CMD_VDU_PUTCH;
        self.machine
            .bus
            .mailbox
            .issue_vdu(CMD_VDU_PUTCH, ch, 0, None);
    }

    pub fn vdu_newline(&mut self) {
        self.vdu_putch(b'\n');
    }

    pub fn vdu_backspace(&mut self) {
        use plover_copro::vdu::{CMD_VDU_GOTO, CMD_VDU_PUTCH, VDU_COLS};
        let vdu = &self.machine.bus.mailbox.vdu;
        if vdu.cursor_col == 0 && vdu.cursor_row == 0 {
            return;
        }
        let col = vdu.cursor_col;
        let row = vdu.cursor_row;
        let (new_col, new_row) = if col > 0 {
            (col - 1, row)
        } else {
            (VDU_COLS as u8 - 1, row.saturating_sub(1))
        };
        self.machine
            .bus
            .mailbox
            .issue_vdu(CMD_VDU_GOTO, new_col, new_row, None);
        self.machine
            .bus
            .mailbox
            .issue_vdu(CMD_VDU_PUTCH, b' ', 0, None);
        self.machine
            .bus
            .mailbox
            .issue_vdu(CMD_VDU_GOTO, new_col, new_row, None);
    }

    pub fn vdu_refresh(&mut self) {
        self.vdu_vsync();
    }

    fn vdu_print_prompt(&mut self, prompt: &str) {
        for &b in prompt.as_bytes() {
            self.vdu_putch(b);
        }
    }

    fn sync_kernel_vdu(&mut self) {
        self.machine.bus.mailbox = self.kernel.bus.mailbox.clone();
    }

    pub fn stage1_boot(&mut self) {
        let mut out = Vec::new();
        self.kernel.boot();
        self.sync_kernel_vdu();
        self.emit("stage1_kernel_ready", &mut out);
    }

    pub fn stage2_shell_start(&mut self) {
        let mut out = Vec::new();
        self.emit("stage2_shell_ready", &mut out);
        self.emit_prompt(&mut out);
        self.vdu_vsync();
    }

    fn emit_prompt(&mut self, acc: &mut Vec<String>) {
        let prompt = self.drives.prompt();
        self.vdu_print_prompt(&prompt);
        self.output.push(prompt.clone());
        acc.push(prompt);
    }

    pub fn sync_mailbox_drives(&mut self) {
        let letters: Vec<char> = self.drives.mounted_letters();
        for letter in letters {
            if let (Some(id), Some(path)) = (
                self.drives.drive_id(letter),
                self.drives.img_path(letter),
            ) {
                if let Ok(data) = std::fs::read(path) {
                    self.machine.bus.mailbox.register_drive_bank(id, &data);
                }
            }
        }
    }

    fn drive_letter_arg(arg: &str) -> Option<char> {
        if arg.len() == 2 && arg.ends_with(':') {
            arg.chars().next()
        } else {
            None
        }
    }

    fn drive_err_msg(e: DriveError) -> String {
        match e {
            DriveError::NotMounted => "ERR drive not mounted".to_string(),
            DriveError::AlreadyMounted => "ERR drive already mounted".to_string(),
            DriveError::CannotUnmountCurrent => "ERR cannot unmount current".to_string(),
            DriveError::BadLetter => "ERR bad drive letter".to_string(),
            DriveError::BadDosPath => "ERR bad path".to_string(),
            other => format!("ERR drive:{other:?}"),
        }
    }

    fn reset_exec_state(&mut self) {
        self.machine.reset_exec_state();
    }

    fn run_plr_bytes(&mut self, plr_name: &str, plr_bytes: &[u8], out: &mut Vec<String>) {
        self.reset_exec_state();
        if let Ok(fs) = self.drives.current_fs_mut() {
            let _ = fs.delete(plr_name);
            if let Err(e) = fs.create(plr_name, plr_bytes) {
                self.emit(&format!("ERR fs:{e:?}"), out);
                return;
            }
        } else {
            self.emit("ERR drive not mounted", out);
            return;
        }
        match self.drives.current_fs() {
            Ok(fs) => match spawn(&mut self.machine, fs, plr_name) {
                Ok(r) => self.emit(&format!("R0_{}", r.r0), out),
                Err(_) => self.emit("ERR spawn", out),
            },
            Err(e) => self.emit(&Self::drive_err_msg(e), out),
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
            self.emit_prompt(&mut out);
            self.vdu_vsync();
            return out;
        }
        if parts.len() == 1 {
            if let Some(letter) = Self::drive_letter_arg(&parts[0]) {
                match self.drives.switch(letter) {
                    Ok(()) => {}
                    Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                }
                self.emit_prompt(&mut out);
                self.vdu_vsync();
                return out;
            }
        }
        let cmd = parts[0].to_ascii_lowercase();
        match cmd.as_str() {
            "dir" => {
                let letter = parts.get(1).and_then(|a| Self::drive_letter_arg(a));
                match self.drives.fs_for(letter) {
                    Ok(fs) => {
                        if let Ok(entries) = fs.list() {
                            for e in entries {
                                let name = String::from_utf8_lossy(&e.name11)
                                    .trim()
                                    .to_string();
                                self.emit(&name, &mut out);
                            }
                        }
                    }
                    Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
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
                        match parse_dos_path(target) {
                            Ok((letter, name)) => {
                                if name.is_empty() {
                                    self.emit("ERR missing filename", &mut out);
                                } else {
                                    self.reset_exec_state();
                                    match self.drives.fs_for(letter) {
                                        Ok(fs) => match spawn(&mut self.machine, fs, name) {
                                            Ok(r) => self.emit(&format!("R0_{}", r.r0), &mut out),
                                            Err(_) => self.emit("ERR spawn", &mut out),
                                        },
                                        Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                                    }
                                }
                            }
                            Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
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
                    match parse_dos_path(&parts[1]) {
                        Ok((letter, name)) if !name.is_empty() => {
                            match self.drives.fs_for(letter) {
                                Ok(fs) => match fs.read(name) {
                                    Ok(data) => self.emit(
                                        &String::from_utf8_lossy(&data).replace('\n', " "),
                                        &mut out,
                                    ),
                                    Err(_) => self.emit("ERR not found", &mut out),
                                },
                                Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                            }
                        }
                        _ => self.emit("ERR missing filename", &mut out),
                    }
                }
            }
            "del" => {
                if parts.len() < 2 {
                    self.emit("ERR missing filename", &mut out);
                } else {
                    match parse_dos_path(&parts[1]) {
                        Ok((letter, name)) if !name.is_empty() => {
                            match self.drives.fs_for_mut(letter) {
                                Ok(fs) => match fs.delete(name) {
                                    Ok(()) => self.emit("OK", &mut out),
                                    Err(_) => self.emit("ERR not found", &mut out),
                                },
                                Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                            }
                        }
                        _ => self.emit("ERR missing filename", &mut out),
                    }
                }
            }
            "mount" => {
                if parts.len() < 3 {
                    self.emit("ERR usage: mount L img", &mut out);
                } else {
                    let letter = parts[1].chars().next().unwrap_or('?');
                    let path = DriveMgr::resolve_img_path(&self.root, &parts[2]);
                    let was_new = !path.exists();
                    match self.drives.mount(letter, path) {
                        Ok(_) => {
                            if was_new {
                                if let Ok(fs) = self.drives.fs_for_mut(Some(letter)) {
                                    let _ = fs.format();
                                }
                            }
                            self.sync_mailbox_drives();
                            self.emit("OK", &mut out);
                        }
                        Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                    }
                }
            }
            "unmount" => {
                if parts.len() < 2 {
                    self.emit("ERR usage: unmount L", &mut out);
                } else {
                    let letter = parts[1].chars().next().unwrap_or('?');
                    match self.drives.unmount(letter) {
                        Ok(()) => {
                            self.sync_mailbox_drives();
                            self.emit("OK", &mut out);
                        }
                        Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
                    }
                }
            }
            "drives" => {
                for letter in self.drives.mounted_letters() {
                    let path = self
                        .drives
                        .img_path(letter)
                        .map(|p| p.file_name().and_then(|n| n.to_str()).unwrap_or("?"))
                        .unwrap_or("?");
                    let cur = if letter == self.drives.current_letter() {
                        " *"
                    } else {
                        ""
                    };
                    self.emit(&format!("{letter}: {path}{cur}"), &mut out);
                }
            }
            "copy" => {
                if parts.len() < 3 {
                    self.emit("ERR usage: copy src dst", &mut out);
                } else {
                    match self.drives.copy(&parts[1], &parts[2]) {
                        Ok(()) => {
                            self.sync_mailbox_drives();
                            self.emit("OK", &mut out);
                        }
                        Err(e) => self.emit(&Self::drive_err_msg(e), &mut out),
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
                    "dir type del run copy mount unmount drives B: ldrun plsrun ccrun mon help exit",
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
        self.emit_prompt(&mut out);
        self.vdu_vsync();
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
                for letter in self.drives.mounted_letters() {
                    let entries = self.drives.fs_for(Some(letter)).ok().and_then(|f| f.list().ok()).unwrap_or_default();
                    let mut used = 2usize;
                    for e in &entries {
                        used += ((e.size_bytes as usize) + 511) / 512;
                    }
                    let cur = if letter == self.drives.current_letter() {
                        '*'
                    } else {
                        ' '
                    };
                    self.emit(
                        &format!(
                            "DRV_{letter}{cur} FILES_{} USED_SECT_{used}",
                            entries.len()
                        ),
                        out,
                    );
                }
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

/// Split at spaces for 40-column console; hard-break overlong tokens.
fn wrap_console_lines(s: &str, width: usize) -> Vec<String> {
    if s.is_empty() {
        return vec![String::new()];
    }
    if s.len() <= width {
        return vec![s.to_string()];
    }
    let mut out = Vec::new();
    let mut line = String::new();
    for word in s.split_whitespace() {
        let extra = if line.is_empty() {
            word.len()
        } else {
            line.len() + 1 + word.len()
        };
        if extra > width {
            if !line.is_empty() {
                out.push(std::mem::take(&mut line));
            }
            let mut remain = word;
            while remain.len() > width {
                out.push(remain[..width].to_string());
                remain = &remain[width..];
            }
            line = remain.to_string();
        } else if line.is_empty() {
            line.push_str(word);
        } else {
            line.push(' ');
            line.push_str(word);
        }
    }
    if !line.is_empty() {
        out.push(line);
    }
    out
}

#[cfg(test)]
mod wrap_tests {
    use super::wrap_console_lines;

    #[test]
    fn wrap_splits_on_spaces() {
        let lines = wrap_console_lines(
            "dir type del run ldrun plsrun ccrun mon help exit",
            40,
        );
        assert!(lines.len() >= 2);
        assert!(lines.iter().all(|l| l.len() <= 40));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::prepare_runtime;

    fn test_img(tag: &str) -> String {
        format!("test_{tag}.img")
    }

    #[test]
    fn help_wrapped_lines_no_blank_row() {
        use plover_copro::vdu::VDU_ROWS;

        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut rt = prepare_runtime(&root, &test_img("help_wrap")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        rt.vdu_newline();
        rt.run_command("help");

        let vdu = &rt.machine.bus.mailbox.vdu;
        let mut rows_with_text = Vec::new();
        for r in 0..VDU_ROWS {
            if vdu.chars[r].iter().any(|&c| c != b' ') {
                rows_with_text.push(r);
            }
        }
        for w in rows_with_text.windows(2) {
            assert_eq!(
                w[1] - w[0],
                1,
                "unexpected blank row between help lines at rows {} and {}",
                w[0],
                w[1]
            );
        }
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
    fn multi_drive_mount_copy() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let mut rt = prepare_runtime(&root, &test_img("multidrive")).unwrap();
        rt.stage1_boot();
        rt.stage2_shell_start();
        let img_b = root.join("hw/fixtures/vfdd/test_multidrive_b.img");
        let _ = std::fs::remove_file(&img_b);
        rt.run_command("mount B test_multidrive_b.img");
        rt.run_command("copy A:README.TXT B:README.TXT");
        rt.run_command("dir B:");
        rt.run_command("B:");
        let out = rt.output.join("\n");
        assert!(out.contains("README"), "{out}");
        assert!(out.contains("B>"), "{out}");
        rt.run_command("unmount B");
        assert!(
            rt.output
                .iter()
                .any(|l| l.contains("ERR cannot unmount current")),
            "{out}"
        );
        let _ = std::fs::remove_file(img_b);
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
        assert!(out.contains("DRV_A") && out.contains("USED_SECT_"), "{out}");
        assert!(out.contains("DEV_SLOT_"), "{out}");
        assert!(out.contains("GPIO_PORTA_"), "{out}");
        assert!(out.contains("SERIAL_SIG_D4"), "{out}");
    }
}
