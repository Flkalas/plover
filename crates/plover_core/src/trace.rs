use std::fs::File;
use std::io::Write;
use std::path::Path;

#[derive(Clone, Debug, Default)]
pub struct TraceEntry {
    pub pc: u16,
    pub phase: u8,
    pub opcode: u8,
    pub cw: u8,
    pub regs: [u8; 4],
    pub halted: bool,
}

#[derive(Default)]
pub struct Tracer {
    entries: Vec<TraceEntry>,
}

impl Tracer {
    pub fn record(
        &mut self,
        pc: u16,
        phase: u8,
        opcode: u8,
        cw: u8,
        regs: [u8; 4],
        halted: bool,
    ) {
        self.entries.push(TraceEntry {
            pc,
            phase,
            opcode,
            cw,
            regs,
            halted,
        });
    }

    pub fn write_jsonl(&self, path: &Path) -> std::io::Result<()> {
        let mut f = File::create(path)?;
        for e in &self.entries {
            let line = serde_json::json!({
                "pc": e.pc,
                "phase": e.phase,
                "opcode": e.opcode,
                "cw": e.cw,
                "regs": e.regs,
                "halted": e.halted,
            });
            writeln!(f, "{line}")?;
        }
        Ok(())
    }
}
