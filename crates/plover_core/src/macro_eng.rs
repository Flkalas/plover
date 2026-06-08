use crate::isa::{
    is_wide_abs16, phase_count, OP_BEQ, OP_CALL, OP_HALT, OP_JMP, OP_MOV, OP_RET, OP_STA16,
};
use crate::micro::MicroEngine;
use plover_mmu::MemoryBus;

pub struct MacroEngine {
    pub bus: MemoryBus,
    pub micro: MicroEngine,
    pub pc: u16,
    pub halted: bool,
    pub fetch_pending: bool,
    current_op: u8,
    current_operand: u16,
    pub ret_stack: Vec<u16>,
}

impl MacroEngine {
    pub fn new(bus: MemoryBus) -> Self {
        let micro = MicroEngine::new(bus.clone());
        Self {
            bus,
            micro,
            pc: 0,
            halted: false,
            fetch_pending: true,
            current_op: 0,
            current_operand: 0,
            ret_stack: Vec::new(),
        }
    }

    fn sync_micro_bus(&mut self) {
        self.micro.bus = self.bus.clone();
    }

    fn pull_micro_bus(&mut self) {
        self.bus = self.micro.bus.clone();
    }

    pub fn fetch_insn(&mut self) {
        self.sync_micro_bus();
        let fa = self.bus.fetch_addr(self.pc);
        let op = self.bus.read_cpu(fa);
        let (operand, insn_len) = if is_wide_abs16(op) {
            let lo = u16::from(self.bus.read_cpu(fa.wrapping_add(1)));
            let hi = u16::from(self.bus.read_cpu(fa.wrapping_add(2)));
            (lo | (hi << 8), 3u16)
        } else {
            let imm = u16::from(self.bus.read_cpu(fa.wrapping_add(1)));
            let len = if matches!(op, OP_RET | OP_HALT) {
                1
            } else {
                2
            };
            (imm, len)
        };
        self.current_op = op;
        self.current_operand = operand;
        let op16 = if is_wide_abs16(op) {
            operand
        } else {
            0
        };
        self.micro.reset_micro(
            op,
            (operand & 0xFF) as u8,
            if op == OP_STA16 { op16 } else { 0 },
        );
        self.pc = fa.wrapping_add(insn_len);
        self.fetch_pending = false;
        if op == OP_HALT {
            self.halted = true;
        }
        self.pull_micro_bus();
    }

    fn apply_macro_side_effects(&mut self) {
        let op = self.current_op;
        let imm = self.current_operand;
        match op {
            OP_BEQ if self.micro.state.flag_z => self.pc = imm,
            OP_JMP => self.pc = imm,
            OP_CALL => {
                self.ret_stack.push(self.pc);
                self.pc = imm;
            }
            OP_RET => {
                if let Some(addr) = self.ret_stack.pop() {
                    self.pc = addr;
                }
            }
            OP_MOV => {
                let dst = ((imm >> 4) & 3) as usize;
                let src = (imm & 3) as usize;
                self.micro.state.regs[dst] = self.micro.state.regs[src];
            }
            _ => {}
        }
    }

    pub fn step(&mut self) {
        if self.halted {
            return;
        }
        if self.fetch_pending {
            self.fetch_insn();
            if self.halted {
                return;
            }
        }
        self.sync_micro_bus();
        self.micro.step();
        self.pull_micro_bus();
        let n = phase_count(self.current_op);
        if self.micro.phases_done(n) {
            self.apply_macro_side_effects();
            self.fetch_pending = true;
            self.micro.state.phase = 0;
        }
    }

    pub fn opcode(&self) -> u8 {
        self.current_op
    }
}
