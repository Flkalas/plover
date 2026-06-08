use crate::fast::MacroFastPath;
use crate::macro_eng::MacroEngine;
use crate::micro::{lookup_cw, MicroEngine};
use crate::trace::Tracer;
use plover_mmu::hex::load_hex;
use plover_mmu::{hex::load_sram_program, CW_FLASH_BASE, MemoryBus};
use std::path::Path;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum EngineKind {
    #[default]
    Micro,
    Macro,
    Fast,
}

impl EngineKind {
    pub fn parse(s: &str) -> Self {
        match s.to_ascii_lowercase().as_str() {
            "macro" => Self::Macro,
            "fast" => Self::Fast,
            _ => Self::Micro,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MachineSnapshot {
    pub pc: u16,
    pub regs: [u8; 4],
    pub halted: bool,
    pub map_mode: u8,
    pub flag_z: bool,
    pub flag_c: bool,
    pub phase: u8,
    pub opcode: u8,
}

pub struct PloverMachine {
    pub bus: MemoryBus,
    pub micro: MicroEngine,
    pub macro_eng: MacroEngine,
    pub fast: MacroFastPath,
    pub engine: EngineKind,
    pub tracer: Tracer,
}

impl PloverMachine {
    pub fn new() -> Self {
        Self::with_engine(EngineKind::Micro)
    }

    pub fn with_engine(engine: EngineKind) -> Self {
        let bus = MemoryBus::default();
        let micro = MicroEngine::new(bus.clone());
        let macro_eng = MacroEngine::new(bus.clone());
        let fast = MacroFastPath::new(bus.clone());
        Self {
            bus,
            micro,
            macro_eng,
            fast,
            engine,
            tracer: Tracer::default(),
        }
    }

    pub fn set_engine(&mut self, engine: EngineKind) {
        self.engine = engine;
    }

    pub fn load_nor(&mut self, path: &Path, offset: usize) {
        self.bus.nor.load_hex_file(path, offset);
        self.sync_all_buses();
    }

    pub fn load_cw(&mut self, path: &Path) {
        let data = load_hex(path, 0);
        if data.is_empty() {
            let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
            let fallback = root.join("hw/fixtures/control/cw.hex");
            let data = load_hex(&fallback, 0);
            self.bus.nor.patch_cw_region(&data, CW_FLASH_BASE);
        } else {
            self.bus.nor.patch_cw_region(&data, CW_FLASH_BASE);
        }
        self.sync_all_buses();
    }

    pub fn load_default_boot_fixtures(&mut self, root: &Path) {
        let boot = root.join("hw/fixtures/boot");
        let rom = boot.join("boot_rom.hex");
        if rom.is_file() {
            self.load_nor(&rom, 0);
        }
        let vec = boot.join("boot_vector.hex");
        if vec.is_file() {
            self.load_nor(&vec, 0xFFFC);
        }
        let cw = root.join("hw/fixtures/control/cw.hex");
        if cw.is_file() {
            self.load_cw(&cw);
        }
    }

    pub fn set_map_mode(&mut self, mode: u8) {
        self.bus.map_mode = mode & 1;
        self.sync_all_buses();
    }

    pub fn set_pc(&mut self, pc: u16) {
        self.fast.pc = pc;
        self.macro_eng.pc = pc;
    }

    pub fn set_regs(&mut self, regs: [u8; 4]) {
        self.fast.regs = regs;
        self.micro.state.regs = regs;
        self.macro_eng.micro.state.regs = regs;
    }

    pub fn regs(&self) -> [u8; 4] {
        match self.engine {
            EngineKind::Fast => self.fast.regs,
            EngineKind::Micro | EngineKind::Macro => self.macro_eng.micro.state.regs,
        }
    }

    pub fn halted(&self) -> bool {
        match self.engine {
            EngineKind::Fast => self.fast.halted,
            EngineKind::Micro | EngineKind::Macro => self.macro_eng.halted,
        }
    }

    pub fn pc(&self) -> u16 {
        match self.engine {
            EngineKind::Fast => self.fast.pc,
            EngineKind::Micro | EngineKind::Macro => self.macro_eng.pc,
        }
    }

    pub fn load_ram(&mut self, data: &[u8], base: u16) {
        self.bus.ram.load(data, base);
        self.sync_all_buses();
    }

    pub fn load_ram_bytes(&mut self, data: &[u8], base: u16) {
        self.load_ram(data, base);
    }

    pub fn reset_exec_state(&mut self) {
        self.fast.regs = [0, 0, 0, 0];
        self.fast.halted = false;
        self.fast.pc = 0;
        self.fast.flag_z = false;
        self.fast.flag_c = false;
        self.micro.state = Default::default();
        self.macro_eng.halted = false;
        self.macro_eng.pc = 0;
        self.macro_eng.fetch_pending = true;
        self.macro_eng.ret_stack.clear();
    }

    pub fn reset(&mut self, map_mode: Option<u8>) {
        if let Some(m) = map_mode {
            self.set_map_mode(m);
        }
        let lo = self.bus.read_cpu(0xFFFC);
        let hi = self.bus.read_cpu(0xFFFD);
        let entry = u16::from(lo) | (u16::from(hi) << 8);
        self.macro_eng.pc = entry;
        self.macro_eng.halted = false;
        self.macro_eng.fetch_pending = true;
        self.macro_eng.ret_stack.clear();
        self.micro.state = Default::default();
        self.fast.pc = entry;
        self.fast.halted = false;
        self.fast.regs = [0, 0, 0, 0];
        self.fast.ret_stack.clear();
        self.sync_all_buses();
    }

    pub fn snapshot(&self) -> MachineSnapshot {
        match self.engine {
            EngineKind::Fast => MachineSnapshot {
                pc: self.fast.pc,
                regs: self.fast.regs,
                map_mode: self.bus.map_mode,
                halted: self.fast.halted,
                flag_z: self.fast.flag_z,
                flag_c: self.fast.flag_c,
                phase: 0,
                opcode: 0,
            },
            EngineKind::Micro | EngineKind::Macro => {
                let st = &self.macro_eng.micro.state;
                MachineSnapshot {
                    pc: self.macro_eng.pc,
                    regs: st.regs,
                    map_mode: self.bus.map_mode,
                    halted: self.macro_eng.halted,
                    flag_z: st.flag_z,
                    flag_c: st.flag_c,
                    phase: st.phase,
                    opcode: self.macro_eng.opcode(),
                }
            }
        }
    }

    pub fn ram_nonzero(&self) -> usize {
        self.bus.ram.nonzero_count()
    }

    pub fn load_ram_program(&mut self, path: &Path, base: u16) {
        let data = load_sram_program(path);
        self.load_ram(&data, base);
    }

    pub fn sync_buses(&mut self) {
        self.sync_all_buses();
    }

    fn sync_all_buses(&mut self) {
        self.fast.bus = self.bus.clone();
        self.micro.bus = self.bus.clone();
        self.macro_eng.bus = self.bus.clone();
        self.macro_eng.micro.bus = self.bus.clone();
    }

    fn pull_bus(&mut self) {
        match self.engine {
            EngineKind::Fast => self.bus = self.fast.bus.clone(),
            EngineKind::Micro | EngineKind::Macro => self.bus = self.macro_eng.bus.clone(),
        }
        self.micro.bus = self.bus.clone();
        self.fast.bus = self.bus.clone();
    }

    pub fn step_once(&mut self) {
        match self.engine {
            EngineKind::Fast => {
                self.sync_all_buses();
                self.fast.step();
                self.pull_bus();
                self.tracer.record(
                    self.fast.pc,
                    0,
                    0,
                    0,
                    self.fast.regs,
                    self.fast.halted,
                );
            }
            EngineKind::Micro | EngineKind::Macro => {
                self.sync_all_buses();
                self.macro_eng.step();
                self.pull_bus();
                self.micro.state = self.macro_eng.micro.state.clone();
                let st = &self.macro_eng.micro.state;
                let op = self.macro_eng.opcode();
                let ph = st.phase.saturating_sub(1);
                let cw = if op != 0 {
                    lookup_cw(|idx| self.bus.nor.read_cw(idx), op, ph).raw
                } else {
                    0
                };
                self.tracer.record(
                    self.macro_eng.pc,
                    st.phase,
                    op,
                    cw,
                    st.regs,
                    self.macro_eng.halted,
                );
            }
        }
    }

    pub fn run(&mut self, max_steps: usize) {
        for _ in 0..max_steps {
            if self.halted() {
                break;
            }
            self.step_once();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn repo_root() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
    }

    fn setup_micro(root: &Path) -> PloverMachine {
        let mut m = PloverMachine::with_engine(EngineKind::Micro);
        m.load_cw(&root.join("hw/fixtures/control/cw.hex"));
        m
    }

    #[test]
    fn add_imm_fast() {
        let root = repo_root();
        let mut m = PloverMachine::with_engine(EngineKind::Fast);
        m.set_map_mode(1);
        m.set_regs([0x12, 0, 0, 0]);
        m.set_pc(0);
        m.load_ram_program(&root.join("hw/fixtures/sram/add_imm.sram.hex"), 0);
        m.run(500);
        assert!(m.halted());
        assert_eq!(m.regs(), [0x12, 0x34, 0x46, 0]);
    }

    #[test]
    fn add_imm_micro() {
        let root = repo_root();
        let mut m = setup_micro(&root);
        m.set_map_mode(1);
        m.set_regs([0x12, 0, 0, 0]);
        m.set_pc(0);
        m.load_ram_program(&root.join("hw/fixtures/sram/add_imm.sram.hex"), 0);
        m.run(500);
        assert!(m.halted());
        assert_eq!(m.regs(), [0x12, 0x34, 0x46, 0]);
    }

    #[test]
    fn call_ret_parity() {
        let root = repo_root();
        let mut m = PloverMachine::with_engine(EngineKind::Fast);
        m.set_map_mode(1);
        m.set_pc(0);
        m.load_ram_program(&root.join("hw/fixtures/sram/call_ret.sram.hex"), 0);
        m.run(200);
        assert!(m.halted());
        assert_eq!(m.regs()[0], 11);
    }

    #[test]
    fn micro_matches_fast_mov() {
        let root = repo_root();
        let prog = root.join("hw/fixtures/sram/add_imm.sram.hex");
        let mut fast = PloverMachine::with_engine(EngineKind::Fast);
        fast.set_map_mode(1);
        fast.set_regs([0x12, 0, 0, 0]);
        fast.set_pc(0);
        fast.load_ram_program(&prog, 0);
        fast.run(500);

        let mut micro = setup_micro(&root);
        micro.set_map_mode(1);
        micro.set_regs([0x12, 0, 0, 0]);
        micro.set_pc(0);
        micro.load_ram_program(&prog, 0);
        micro.run(500);

        assert_eq!(fast.regs(), micro.regs());
        assert_eq!(fast.halted(), micro.halted());
    }
}
