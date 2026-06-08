use plover_copro::apu::{CMD_APU_CH_WRITE, CMD_APU_SET_CTRL, WAVE_SQUARE};
use plover_copro::vdu::{
    CMD_GFX_FILLRECT, CMD_GFX_PLOT, CMD_VDU_CLS, CMD_VDU_GOTO, CMD_VDU_PRINT, CMD_VDU_VSYNC,
};
use plover_mmu::MemoryBus;
use std::collections::HashMap;

#[derive(Debug)]
pub struct ForthError(pub String);

impl std::fmt::Display for ForthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for ForthError {}

type WordFn = fn(&mut Forth);

#[derive(Clone)]
enum WordKind {
    Native(WordFn),
    Colon(usize),
}

#[derive(Debug, Clone)]
pub struct ForthScenarioResult {
    pub ok: bool,
    pub output: Vec<String>,
    pub stack: Vec<u16>,
    pub error: Option<String>,
}

pub struct Forth {
    pub data: Vec<u16>,
    pub rstack: Vec<u16>,
    dict: HashMap<String, WordKind>,
    colon_bodies: Vec<Vec<String>>,
    pub output: Vec<String>,
    blocks: HashMap<u16, Vec<u8>>,
    pub input_bytes: Vec<u8>,
    compile: Option<Vec<String>>,
    compile_name: Option<String>,
    bus: Option<MemoryBus>,
}

impl Forth {
    pub fn new(bus: Option<MemoryBus>) -> Self {
        let mut f = Self {
            data: Vec::new(),
            rstack: Vec::new(),
            dict: HashMap::new(),
            colon_bodies: Vec::new(),
            output: Vec::new(),
            blocks: HashMap::new(),
            input_bytes: Vec::new(),
            compile: None,
            compile_name: None,
            bus,
        };
        f.install_core();
        f
    }

    fn install_core(&mut self) {
        self.word("DUP", |f| {
            let v = f.data.last().copied().unwrap_or(0);
            f.push(v);
        });
        self.word("DROP", |f| {
            f.pop().ok();
        });
        self.word("SWAP", |f| {
            let b = f.pop().unwrap_or(0);
            let a = f.pop().unwrap_or(0);
            f.push(b);
            f.push(a);
        });
        self.word("+", |f| {
            let b = f.pop().unwrap_or(0);
            let a = f.pop().unwrap_or(0);
            f.push(a.wrapping_add(b));
        });
        self.word("-", |f| {
            let b = f.pop().unwrap_or(0);
            let a = f.pop().unwrap_or(0);
            f.push(a.wrapping_sub(b));
        });
        self.word("*", |f| {
            let b = f.pop().unwrap_or(0);
            let a = f.pop().unwrap_or(0);
            f.push(a.wrapping_mul(b));
        });
        self.word(".", |f| {
            let v = f.pop().unwrap_or(0);
            f.emit(&v.to_string());
        });
        self.word("EMIT", |f| f.w_emit());
        self.word("KEY", |f| {
            let _ = f.w_key();
        });
        self.word("BLK@", |f| f.w_blk_fetch());
        self.word("BLK!", |f| f.w_blk_store());
        self.word("FLUSH", |_f| {});
        if self.bus.is_some() {
            self.word("VCLS", |f| f.w_vcls());
            self.word("VPUT", |f| f.w_vput());
            self.word("VGOTO", |f| f.w_vgoto());
            self.word("GPLOT", |f| f.w_gplot());
            self.word("GRECT", |f| f.w_grect());
            self.word("GVSYNC", |f| f.w_gvsync());
            self.word("BEEP", |f| f.w_beep());
            self.word("MOUSE?", |f| f.w_mouse_q());
        }
    }

    fn word(&mut self, name: &str, code: WordFn) {
        self.dict
            .insert(name.to_ascii_uppercase(), WordKind::Native(code));
    }

    fn run_colon(&mut self, idx: usize) -> Result<(), ForthError> {
        let body = self.colon_bodies[idx].clone();
        for t in &body {
            self.run_token(t)?;
        }
        Ok(())
    }

    pub fn emit(&mut self, s: &str) {
        self.output.push(s.to_string());
    }

    pub fn pop(&mut self) -> Result<u16, ForthError> {
        self.data.pop().ok_or_else(|| ForthError("stack underflow".into()))
    }

    pub fn push(&mut self, v: u16) {
        self.data.push(v & 0xFFFF);
    }

    fn w_emit(&mut self) {
        let v = self.pop().unwrap_or(0) as u8;
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_VDU_PRINT, 1, 0, Some(&[v]));
        }
        self.emit(&char::from(v).to_string());
    }

    fn w_vcls(&mut self) {
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_VDU_CLS, 7, 0, None);
        }
    }

    fn w_vput(&mut self) {
        let ch = self.pop().unwrap_or(0) as u8;
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_VDU_PRINT, 1, 0, Some(&[ch]));
        }
    }

    fn w_vgoto(&mut self) {
        let row = self.pop().unwrap_or(0) as u8;
        let col = self.pop().unwrap_or(0) as u8;
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_VDU_GOTO, col, row, None);
        }
    }

    fn w_gplot(&mut self) {
        let color = self.pop().unwrap_or(0);
        let y = self.pop().unwrap_or(0) as u8;
        let x = self.pop().unwrap_or(0) as u8;
        let buf = [x, y, (color & 0xFF) as u8, (color >> 8) as u8];
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_GFX_PLOT, 0, 0, Some(&buf));
        }
    }

    fn w_grect(&mut self) {
        let color = self.pop().unwrap_or(0);
        let h = self.pop().unwrap_or(0) as u8;
        let w = self.pop().unwrap_or(0) as u8;
        let y = self.pop().unwrap_or(0) as u8;
        let x = self.pop().unwrap_or(0) as u8;
        let buf = [x, y, w, h, (color & 0xFF) as u8, (color >> 8) as u8];
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_GFX_FILLRECT, 0, 0, Some(&buf));
        }
    }

    fn w_gvsync(&mut self) {
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);
        }
    }

    fn w_beep(&mut self) {
        let duration = self.pop().unwrap_or(0);
        let period = self.pop().unwrap_or(0);
        if let Some(bus) = self.bus.as_mut() {
            bus.mailbox.issue_apu(CMD_APU_SET_CTRL, 0, Some(&[15, 0]));
            bus.mailbox.issue_apu(
                CMD_APU_CH_WRITE,
                0,
                Some(&[
                    0,
                    (period & 0xFF) as u8,
                    (period >> 8) as u8,
                    15,
                    WAVE_SQUARE,
                ]),
            );
            let _ = duration;
        }
    }

    fn w_key(&mut self) -> Result<(), ForthError> {
        if let Some(bus) = self.bus.as_ref() {
            if bus.mailbox.hid.key_pending() {
                self.push(u16::from(bus.mailbox.hid.last_key));
                return Ok(());
            }
        }
        if self.input_bytes.is_empty() {
            return Err(ForthError("KEY: no input".into()));
        }
        let b = self.input_bytes.remove(0);
        self.push(u16::from(b));
        Ok(())
    }

    fn w_mouse_q(&mut self) {
        if let Some(bus) = self.bus.as_ref() {
            if bus.mailbox.hid.mouse_pending() {
                let ev = bus.mailbox.hid.last_mouse;
                self.push(u16::from(ev.buttons));
                self.push(ev.dx as u16);
                self.push(ev.dy as u16);
                return;
            }
        }
        self.push(0);
        self.push(0);
        self.push(0);
    }

    fn get_block(&mut self, n: u16) -> &mut Vec<u8> {
        self.blocks.entry(n).or_insert_with(|| vec![0u8; 256])
    }

    fn w_blk_fetch(&mut self) {
        let off = self.pop().unwrap_or(0) as usize;
        let blk = self.pop().unwrap_or(0);
        let val = self
            .blocks
            .get(&blk)
            .and_then(|b| b.get(off))
            .copied()
            .unwrap_or(0);
        self.push(u16::from(val));
    }

    fn w_blk_store(&mut self) {
        let off = self.pop().unwrap_or(0) as usize;
        let blk = self.pop().unwrap_or(0);
        let val = self.pop().unwrap_or(0) as u8;
        let b = self.get_block(blk);
        if off < b.len() {
            b[off] = val;
        }
    }

    fn run_token(&mut self, tok: &str) -> Result<(), ForthError> {
        let u = tok.to_ascii_uppercase();
        if let Some(w) = self.dict.get(&u).cloned() {
            return match w {
                WordKind::Native(code) => {
                    code(self);
                    Ok(())
                }
                WordKind::Colon(idx) => self.run_colon(idx),
            };
        }
        if let Ok(n) = parse_num(tok) {
            self.push(n);
            return Ok(());
        }
        Err(ForthError(format!("unknown word: {tok}")))
    }

    pub fn eval_line(&mut self, line: &str) -> Result<(), ForthError> {
        let toks: Vec<&str> = line
            .split_whitespace()
            .filter(|t| !t.is_empty())
            .collect();
        let mut i = 0;
        while i < toks.len() {
            let tok = toks[i];
            let u = tok.to_ascii_uppercase();
            if u == ":" {
                if i + 1 >= toks.len() {
                    return Err(ForthError("missing word name after ':'".into()));
                }
                self.compile = Some(Vec::new());
                self.compile_name = Some(toks[i + 1].to_ascii_uppercase());
                i += 2;
                continue;
            }
            if u == ";" {
                let body = self.compile.take().ok_or_else(|| ForthError("';' outside definition".into()))?;
                let name = self
                    .compile_name
                    .take()
                    .ok_or_else(|| ForthError("';' outside definition".into()))?;
                let idx = self.colon_bodies.len();
                self.colon_bodies.push(body);
                self.dict.insert(name, WordKind::Colon(idx));
                i += 1;
                continue;
            }
            if self.compile.is_some() {
                self.compile.as_mut().unwrap().push(tok.to_string());
            } else {
                self.run_token(tok)?;
            }
            i += 1;
        }
        Ok(())
    }
}

fn parse_num(tok: &str) -> Result<u16, ()> {
    let t = tok.trim();
    if let Some(hex) = t.strip_prefix("0x").or_else(|| t.strip_prefix("0X")) {
        u16::from_str_radix(hex, 16).map_err(|_| ())
    } else if let Some(oct) = t.strip_prefix("0o") {
        u16::from_str_radix(oct, 8).map_err(|_| ())
    } else {
        t.parse::<u16>().map_err(|_| ())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stack_ops() {
        let mut f = Forth::new(None);
        f.eval_line("1 2 SWAP").unwrap();
        assert_eq!(f.data, vec![2, 1]);
        f.eval_line("DUP").unwrap();
        assert_eq!(f.data, vec![2, 1, 1]);
        f.eval_line("DROP").unwrap();
        assert_eq!(f.data, vec![2, 1]);
    }

    #[test]
    fn arith() {
        let mut f = Forth::new(None);
        f.eval_line("2 3 +").unwrap();
        assert_eq!(f.data, vec![5]);
        f.eval_line("10 4 -").unwrap();
        assert_eq!(f.data, vec![5, 6]);
        f.eval_line("6 7 *").unwrap();
        assert_eq!(f.data.last(), Some(&42));
    }

    #[test]
    fn colon_def() {
        let mut f = Forth::new(None);
        f.eval_line(": SQUARE DUP * ;").unwrap();
        f.eval_line("5 SQUARE .").unwrap();
        assert_eq!(f.output, vec!["25"]);
    }
}
