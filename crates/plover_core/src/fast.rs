use crate::alu::{apply_add, apply_beq_compare, apply_cmp_flags, alu8};
use crate::alu16::{add16, cmp16_u};
use crate::isa::*;
use plover_mmu::{mmio_addr, MemoryBus};

pub struct MacroFastPath {
    pub bus: MemoryBus,
    pub pc: u16,
    pub regs: [u8; 4],
    pub regs16: [u16; 4],
    pub flag_z: bool,
    pub flag_c: bool,
    pub halted: bool,
    pub ret_stack: Vec<u16>,
}

impl MacroFastPath {
    pub fn new(bus: MemoryBus) -> Self {
        Self {
            bus,
            pc: 0,
            regs: [0; 4],
            regs16: [0; 4],
            flag_z: false,
            flag_c: false,
            halted: false,
            ret_stack: Vec::new(),
        }
    }

    fn read_byte(&self, addr: u16) -> u8 {
        self.bus.read_cpu(addr)
    }

    pub fn fetch_decode_execute(&mut self) {
        if self.halted {
            return;
        }
        let fa = self.bus.fetch_addr(self.pc);
        let op = self.read_byte(fa);

        let (imm, wide_imm16): (u16, bool) = if is_wide_imm16(op) {
            let v = u16::from(self.read_byte(fa.wrapping_add(1)))
                | (u16::from(self.read_byte(fa.wrapping_add(2))) << 8);
            self.pc = fa.wrapping_add(3);
            (v, true)
        } else if is_wide_abs16(op) {
            let v = u16::from(self.read_byte(fa.wrapping_add(1)))
                | (u16::from(self.read_byte(fa.wrapping_add(2))) << 8);
            self.pc = fa.wrapping_add(3);
            (v, false)
        } else if matches!(op, OP_RET | OP_HALT | OP_ADD_RR) {
            self.pc = fa.wrapping_add(1);
            (0, false)
        } else {
            let v = u16::from(self.read_byte(fa.wrapping_add(1)));
            self.pc = fa.wrapping_add(2);
            (v, false)
        };

        match op {
            OP_HALT => self.halted = true,
            OP_ADD => {
                let (r, z, c) = apply_add(self.regs, imm as u8);
                self.regs = r;
                self.flag_z = z;
                self.flag_c = c;
            }
            OP_ADD_RR => {
                let res = alu8(self.regs[0], self.regs[1], 1);
                self.regs[2] = res.y;
                self.flag_z = res.zero;
                self.flag_c = res.cout;
            }
            OP_MOV => {
                let dst = ((imm >> 4) & 3) as usize;
                let src = (imm & 3) as usize;
                self.regs[dst] = self.regs[src];
            }
            OP_CMP => {
                let (z, c) = apply_cmp_flags(self.regs, imm as u8);
                self.flag_z = z;
                self.flag_c = c;
            }
            OP_WADD_RR => {
                let res = add16(self.regs16[0], self.regs16[1]);
                self.regs16[2] = res.y;
                self.flag_z = res.zero;
                self.flag_c = res.cout;
            }
            OP_WMOV => {
                let dst = ((imm >> 4) & 3) as usize;
                let src = (imm & 3) as usize;
                self.regs16[dst] = self.regs16[src];
            }
            OP_WCMP16 if wide_imm16 => {
                let res = cmp16_u(self.regs16[0], imm);
                self.flag_z = res.zero;
                self.flag_c = res.cout;
            }
            OP_BCS => {
                if self.flag_c {
                    self.pc = imm;
                }
            }
            OP_LDA => self.regs[0] = self.read_byte(imm as u16),
            OP_STA | OP_STA16 => self.bus.write_cpu(imm as u16, self.regs[0]),
            OP_BEQ => {
                let (z, c) = apply_beq_compare(self.regs, imm as u8);
                self.flag_z = z;
                self.flag_c = c;
                if self.flag_z {
                    self.pc = imm;
                }
            }
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
            OP_LDIO => self.regs[0] = self.read_byte(mmio_addr(imm as u8)),
            OP_STIO => self.bus.write_cpu(mmio_addr(imm as u8), self.regs[0]),
            _ => {}
        }
    }

    pub fn step(&mut self) {
        self.fetch_decode_execute();
    }

    pub fn run(&mut self, max_steps: usize) {
        for _ in 0..max_steps {
            if self.halted {
                break;
            }
            self.step();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use plover_mmu::MB_STATUS;

    #[test]
    fn ldio_stio_parity() {
        let mut bus = MemoryBus::default();
        bus.map_mode = 1;
        let mut fast = MacroFastPath::new(bus);
        fast.regs[0] = 0xAB;
        fast.pc = 0;
        let prog = [OP_LDIO, 0x00, OP_STIO, 0x04, OP_HALT];
        for (i, &b) in prog.iter().enumerate() {
            fast.bus.ram.write(i as u16, b);
        }
        fast.run(10);
        assert_eq!(fast.regs[0], 0x08); // APU_READY on idle status
        assert_eq!(fast.bus.mailbox.read(MB_STATUS), 0x08);
    }
}
