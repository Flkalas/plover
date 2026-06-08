use std::collections::VecDeque;

pub const CMD_HID_POLL: u8 = 0x40;
pub const CMD_HID_KEY_READ: u8 = 0x41;
pub const CMD_HID_MOUSE_READ: u8 = 0x42;
pub const CMD_HID_INJECT: u8 = 0x43;

pub const INJECT_KEY: u8 = 0;
pub const INJECT_MOUSE: u8 = 1;

pub const KEY_MAX: usize = 64;
pub const MOUSE_MAX: usize = 32;

#[derive(Clone, Copy, Default, Debug, PartialEq, Eq)]
pub struct MouseEvent {
    pub buttons: u8,
    pub dx: i8,
    pub dy: i8,
}

#[derive(Clone, Debug, Default)]
pub struct HidState {
    key_queue: VecDeque<u8>,
    mouse_queue: VecDeque<MouseEvent>,
    pub last_key: u8,
    pub last_mouse: MouseEvent,
}

impl HidState {
    pub fn key_pending(&self) -> bool {
        !self.key_queue.is_empty()
    }

    pub fn mouse_pending(&self) -> bool {
        !self.mouse_queue.is_empty()
    }

    pub fn key_queue_len(&self) -> usize {
        self.key_queue.len()
    }

    pub fn enqueue_key(&mut self, ch: u8) {
        if self.key_queue.len() >= KEY_MAX {
            self.key_queue.pop_front();
        }
        self.key_queue.push_back(ch);
    }

    pub fn enqueue_mouse(&mut self, buttons: u8, dx: i8, dy: i8) {
        if self.mouse_queue.len() >= MOUSE_MAX {
            self.mouse_queue.pop_front();
        }
        self.mouse_queue.push_back(MouseEvent {
            buttons: buttons & 0x07,
            dx,
            dy,
        });
    }

    fn poll(&mut self, buffer: &mut [u8; 248]) -> bool {
        buffer[0] = (self.key_queue.len().min(255)) as u8;
        buffer[1] = (self.mouse_queue.len().min(255)) as u8;
        true
    }

    fn read_key(&mut self, buffer: &mut [u8; 248]) -> bool {
        self.last_key = self.key_queue.pop_front().unwrap_or(0);
        buffer[0] = self.last_key;
        true
    }

    fn read_mouse(&mut self, buffer: &mut [u8; 248]) -> bool {
        if let Some(ev) = self.mouse_queue.pop_front() {
            self.last_mouse = ev;
            buffer[0] = ev.buttons;
            buffer[1] = ev.dx as u8;
            buffer[2] = ev.dy as u8;
        } else {
            self.last_mouse = MouseEvent::default();
            buffer[0] = 0;
            buffer[1] = 0;
            buffer[2] = 0;
        }
        true
    }

    fn inject(&mut self, buffer: &[u8]) -> bool {
        if buffer.len() < 2 {
            return false;
        }
        match buffer[0] {
            INJECT_KEY => {
                self.enqueue_key(buffer[1]);
                true
            }
            INJECT_MOUSE if buffer.len() >= 4 => {
                self.enqueue_mouse(
                    buffer[1],
                    sign8(buffer[2]),
                    sign8(buffer[3]),
                );
                true
            }
            _ => false,
        }
    }

    pub fn dispatch(&mut self, cmd: u8, buffer: &mut [u8; 248], payload_len: usize) -> bool {
        let payload = &buffer[..payload_len.min(buffer.len())];
        match cmd {
            CMD_HID_POLL => self.poll(buffer),
            CMD_HID_KEY_READ => self.read_key(buffer),
            CMD_HID_MOUSE_READ => self.read_mouse(buffer),
            CMD_HID_INJECT => self.inject(payload),
            _ => false,
        }
    }
}

fn sign8(v: u8) -> i8 {
    let x = v as i16;
    if x < 128 {
        x as i8
    } else {
        (x - 256) as i8
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hid_inject_read_key() {
        let mut hid = HidState::default();
        let mut buf = [0u8; 248];
        buf[0] = INJECT_KEY;
        buf[1] = b'Z';
        assert!(hid.dispatch(CMD_HID_INJECT, &mut buf, 2));
        assert!(hid.key_pending());
        hid.dispatch(CMD_HID_POLL, &mut buf, 248);
        assert_eq!(buf[0], 1);
        hid.dispatch(CMD_HID_KEY_READ, &mut buf, 248);
        assert_eq!(buf[0], b'Z');
        assert!(!hid.key_pending());
    }

    #[test]
    fn hid_inject_read_mouse() {
        let mut hid = HidState::default();
        let mut buf = [0u8; 248];
        buf[..4].copy_from_slice(&[INJECT_MOUSE, 0x01, 0xFE, 0x05]);
        assert!(hid.dispatch(CMD_HID_INJECT, &mut buf, 4));
        assert!(hid.mouse_pending());
        hid.dispatch(CMD_HID_MOUSE_READ, &mut buf, 248);
        assert_eq!(buf[0], 0x01);
        assert_eq!(buf[1], 0xFE);
        assert_eq!(buf[2], 0x05);
    }

    #[test]
    fn hid_overflow_drop_oldest() {
        let mut hid = HidState::default();
        for i in 0..(KEY_MAX + 5) {
            hid.enqueue_key(0x30 + (i % 10) as u8);
        }
        assert_eq!(hid.key_queue_len(), KEY_MAX);
        let mut buf = [0u8; 248];
        hid.dispatch(CMD_HID_KEY_READ, &mut buf, 248);
        assert_eq!(buf[0], 0x30 + 5);
    }

    #[test]
    fn hid_invalid_inject() {
        let mut hid = HidState::default();
        let mut buf = [0u8; 248];
        buf[..2].copy_from_slice(&[99, 0]);
        assert!(!hid.dispatch(CMD_HID_INJECT, &mut buf, 2));
        buf[..2].copy_from_slice(&[INJECT_MOUSE, 0]);
        assert!(!hid.dispatch(CMD_HID_INJECT, &mut buf, 2));
    }
}
