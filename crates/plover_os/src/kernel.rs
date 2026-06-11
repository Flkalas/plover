use plover_mmu::MemoryBus;
use std::collections::BTreeMap;

pub const SIG_FDD: u8 = 0xA1;
pub const SIG_GPIO: u8 = 0xC3;
pub const SIG_UART: u8 = 0xD4;
pub const SIG_VIDEO: u8 = 0x56;
pub const SIG_AUDIO: u8 = 0x41;
pub const SIG_HID: u8 = 0x48;

#[derive(Clone, Debug, Default)]
pub struct GpioController {
    pub direction: u8,
    pub port_a: u8,
}

impl GpioController {
    pub fn read_port(&self) -> u8 {
        self.port_a & 0xFF
    }

    pub fn set_input_bits(&mut self, mask: u8, values: u8) {
        self.port_a = (self.port_a & !mask) | (values & mask);
    }

    pub fn get_bit(&self, bit: u8) -> bool {
        (self.port_a >> bit) & 1 != 0
    }

    pub fn set_bit(&mut self, bit: u8) {
        self.port_a |= 1 << bit;
    }

    pub fn clear_bit(&mut self, bit: u8) {
        self.port_a &= !(1 << bit);
    }
}

#[derive(Clone, Debug, Default)]
pub struct SerialModule {
    pub signature: u8,
    pub tx_fifo: Vec<u8>,
    pub rx_fifo: Vec<u8>,
}

impl SerialModule {
    pub fn new() -> Self {
        Self {
            signature: SIG_UART,
            ..Default::default()
        }
    }

    pub fn status(&self) -> u8 {
        let mut st = 0x02; // ST_TX_READY
        if !self.rx_fifo.is_empty() {
            st |= 0x01; // ST_RX_READY
        }
        st
    }

    pub fn write(&mut self, data: &[u8]) {
        self.tx_fifo.extend_from_slice(data);
    }
}

#[derive(Clone, Debug, Default)]
pub struct KernelState {
    pub slot_signatures: BTreeMap<u8, u8>,
    pub device_table: BTreeMap<u8, String>,
    pub output: Vec<String>,
}

pub struct Kernel {
    pub bus: MemoryBus,
    pub state: KernelState,
    pub gpio: GpioController,
    pub serial: SerialModule,
}

impl Kernel {
    pub fn new(bus: MemoryBus) -> Self {
        Self {
            bus,
            state: KernelState::default(),
            gpio: GpioController {
                direction: 0x0F,
                port_a: 0,
            },
            serial: SerialModule::new(),
        }
    }

    pub fn kprint(&mut self, s: &str) {
        self.state.output.push(s.to_string());
        self.serial.write(&(s.to_string() + "\n").into_bytes());
        let mut text = s.to_string();
        text.push('\n');
        let bytes = text.as_bytes();
        let len = bytes.len().min(255) as u8;
        use plover_copro::vdu::CMD_VDU_PRINT;
        self.bus.mailbox.issue_vdu(CMD_VDU_PRINT, len, 0, Some(bytes));
    }

    pub fn devmgr_scan(&mut self) {
        self.state.device_table.clear();
        let sigs: BTreeMap<u8, u8> = if self.state.slot_signatures.is_empty() {
            [
                (0, SIG_FDD),
                (1, SIG_GPIO),
                (2, SIG_UART),
                (3, SIG_VIDEO),
                (4, SIG_AUDIO),
                (5, SIG_HID),
            ]
            .into_iter()
            .collect()
        } else {
            self.state.slot_signatures.clone()
        };
        for (idx, sig) in sigs {
            if sig == 0x00 || sig == 0xFF {
                continue;
            }
            let drv = match sig {
                SIG_FDD => "vfdd",
                SIG_GPIO => "gpio",
                SIG_UART => "serial",
                SIG_VIDEO => "video",
                SIG_AUDIO => "audio",
                SIG_HID => "hid",
                _ => "unknown",
            };
            self.state.device_table.insert(idx, drv.to_string());
            self.kprint(&format!("DEV slot{idx} sig={sig:02X} drv={drv}"));
        }
    }

    pub fn boot(&mut self) {
        if self.state.slot_signatures.is_empty() {
            self.state.slot_signatures = [
                (0, SIG_FDD),
                (1, SIG_GPIO),
                (2, SIG_UART),
                (3, SIG_VIDEO),
                (4, SIG_AUDIO),
                (5, SIG_HID),
            ]
            .into_iter()
            .collect();
        }
        self.kprint("kernel_boot");
        self.devmgr_scan();
        self.kprint("kernel_help");
    }
}
