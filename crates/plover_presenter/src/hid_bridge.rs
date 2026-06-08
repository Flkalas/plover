use plover_copro::hid::{INJECT_KEY, INJECT_MOUSE};
use plover_copro::Mailbox;

pub struct HidBridge;

impl HidBridge {
    pub fn inject_key(mb: &mut Mailbox, ch: u8) {
        mb.issue_hid(0x43, Some(&[INJECT_KEY, ch]));
    }

    pub fn inject_mouse(mb: &mut Mailbox, buttons: u8, dx: i8, dy: i8) {
        mb.issue_hid(
            0x43,
            Some(&[INJECT_MOUSE, buttons, dx as u8, dy as u8]),
        );
    }
}
