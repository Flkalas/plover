mod cw;
mod reg_sel;

pub use cw::lookup_cw;

use crate::alu::alu8;
use crate::isa::{OP_LDIO, OP_STA16, OP_STIO};
use plover_mmu::{mmio_addr, MemoryBus};

#[derive(Clone, Debug, Default)]
pub struct MicroState {
    pub opcode: u8,
    pub operand: u8,
    pub operand16: u16,
    pub phase: u8,
    pub regs: [u8; 4],
    pub alu_a: u8,
    pub alu_b: u8,
    pub alu_y: u8,
    pub bus_data: u8,
    pub eff_addr: u16,
    pub flag_z: bool,
    pub flag_c: bool,
}

pub struct MicroEngine {
    pub bus: MemoryBus,
    pub state: MicroState,
}

impl MicroEngine {
    pub fn new(bus: MemoryBus) -> Self {
        Self {
            bus,
            state: MicroState::default(),
        }
    }

    pub fn reset_micro(&mut self, opcode: u8, operand: u8, operand16: u16) {
        self.state.opcode = opcode;
        self.state.operand = operand;
        self.state.operand16 = operand16;
        self.state.phase = 0;
        self.state.alu_a = 0;
        self.state.alu_b = 0;
    }

    pub fn step(&mut self) {
        let op = self.state.opcode;
        let ph = self.state.phase;
        let cw = lookup_cw(|idx| self.bus.nor.read_cw(idx), op, ph);
        let sel = cw.reg_sel();

        if cw.mem_rd() {
            if op == OP_LDIO {
                self.state.eff_addr = mmio_addr(self.state.operand);
            } else {
                self.state.eff_addr = u16::from(self.state.operand);
            }
            self.state.bus_data = self.bus.read_cpu(self.state.eff_addr);
        }

        if op == 0x01 && cw.alu_op() != 0 {
            if ph == 0 && self.state.operand != 0 {
                self.state.regs[1] = self.state.operand;
            }
            let res = alu8(self.state.regs[0], self.state.regs[1], cw.alu_op());
            self.state.alu_y = res.y;
            self.state.flag_z = res.zero;
            self.state.flag_c = res.cout;
        } else if cw.y_oe() || cw.alu_op() != 0 {
            let ra = if sel < 4 {
                self.state.regs[sel as usize]
            } else {
                0
            };
            self.state.alu_a = ra;
            let res = alu8(self.state.alu_a, self.state.alu_b, cw.alu_op());
            self.state.alu_y = res.y;
            self.state.flag_z = res.zero;
            self.state.flag_c = res.cout;
        }

        if cw.reg_we() && sel < 4 {
            let idx = sel as usize;
            if matches!(op, 0x02 | OP_LDIO) && ph == 1 {
                self.state.regs[idx] = self.state.bus_data;
            } else {
                self.state.regs[idx] = self.state.alu_y;
            }
        }

        if cw.mem_wr() {
            let val = if cw.y_oe() {
                self.state.alu_y
            } else {
                self.state.regs[0]
            };
            let addr = if op == OP_STIO {
                mmio_addr(self.state.operand)
            } else if op == OP_STA16 {
                self.state.operand16
            } else if self.state.eff_addr != 0 {
                self.state.eff_addr
            } else {
                u16::from(self.state.operand)
            };
            self.bus.write_cpu(addr, val);
        }

        self.state.phase = self.state.phase.saturating_add(1);
    }

    pub fn phases_done(&self, phase_count: usize) -> bool {
        self.state.phase as usize >= phase_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use plover_mmu::{hex::load_hex, CW_FLASH_BASE};
    use std::path::PathBuf;

    fn load_cw(bus: &mut MemoryBus) {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let data = load_hex(&root.join("hw/fixtures/control/cw.hex"), 0);
        bus.nor.patch_cw_region(&data, CW_FLASH_BASE);
    }

    #[test]
    fn add_r0_r1_to_r2() {
        let mut bus = MemoryBus::default();
        load_cw(&mut bus);
        let mut micro = MicroEngine::new(bus);
        micro.reset_micro(0x01, 0, 0);
        micro.state.regs = [3, 5, 0, 0];
        for _ in 0..3 {
            micro.step();
        }
        assert_eq!(micro.state.regs[2], 8);
    }
}
