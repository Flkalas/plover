use plover_core::{EngineKind, PloverMachine};
use plover_copro::apu::{CMD_APU_CH_WRITE, CMD_APU_SET_CTRL, WAVE_SQUARE};
use plover_copro::hid::{CMD_HID_INJECT, CMD_HID_MOUSE_READ, INJECT_KEY, INJECT_MOUSE};
use plover_copro::vdu::{CMD_GFX_FILLRECT, CMD_GFX_PLOT, CMD_VDU_CLS, CMD_VDU_PRINT, CMD_VDU_VSYNC};
use std::path::Path;

pub fn cmd_vdu_demo(root: &Path) -> i32 {
    let mut m = PloverMachine::with_engine(EngineKind::Fast);
    m.load_cw(&root.join("hw/fixtures/control/cw.hex"));
    let mb = &mut m.bus.mailbox;
    mb.issue_vdu(CMD_VDU_CLS, 7, 0, None);
    mb.issue_vdu(CMD_VDU_PRINT, 15, 0, Some(b"PLOVER VDU DEMO"));
    let buf = [10u8, 10, 40, 30, 0x1F, 0x00];
    mb.issue_vdu(CMD_GFX_FILLRECT, 0, 0, Some(&buf));
    let plot = [50u8, 50, 0x00, 0xF8];
    mb.issue_vdu(CMD_GFX_PLOT, 0, 0, Some(&plot));
    mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);
    let text = m.bus.mailbox.vdu.compose_text();
    let line0 = text.lines().next().unwrap_or("").chars().take(40).collect::<String>();
    println!("{line0}");
    let px = m.bus.mailbox.vdu.bitmap[10 * 320 + 10];
    println!("frame={} pixel@10,10=0x{px:04X}", m.bus.mailbox.vdu.frame);
    0
}

pub fn cmd_apu_demo(root: &Path) -> i32 {
    let mut m = PloverMachine::with_engine(EngineKind::Fast);
    m.load_cw(&root.join("hw/fixtures/control/cw.hex"));
    let mb = &mut m.bus.mailbox;
    mb.issue_apu(CMD_APU_SET_CTRL, 0, Some(&[15, 0]));
    mb.issue_apu(CMD_APU_CH_WRITE, 0, Some(&[0, 22, 0, 15, WAVE_SQUARE]));
    let apu = &m.bus.mailbox.apu;
    let mut apu_mut = apu.clone();
    let samples = apu_mut.mix_samples(100);
    let peak = samples
        .iter()
        .map(|&b| (i32::from(b) - 128).unsigned_abs())
        .max()
        .unwrap_or(0);
    println!(
        "ch0 period={} vol={}",
        apu.channels[0].period, apu.channels[0].volume
    );
    println!("mix peak deviation={peak} apu_ready={}", apu.master_vol != 0);
    0
}

pub fn cmd_hid_demo(root: &Path) -> i32 {
    let mut m = PloverMachine::with_engine(EngineKind::Fast);
    m.load_cw(&root.join("hw/fixtures/control/cw.hex"));
    let mb = &mut m.bus.mailbox;
    mb.issue_hid(CMD_HID_INJECT, Some(&[INJECT_KEY, b'H']));
    mb.issue_hid(CMD_HID_INJECT, Some(&[INJECT_MOUSE, 0x01, 5, 0xFD]));
    mb.issue_hid(CMD_HID_MOUSE_READ, None);
    let hid = &m.bus.mailbox.hid;
    let kd = hid.key_pending();
    let md = hid.mouse_pending();
    let ch = hid.last_key;
    let ev = hid.last_mouse;
    println!(
        "poll key={kd} mouse={md} char={} btn={} dx={} dy={}",
        char::from(ch),
        ev.buttons,
        ev.dx,
        ev.dy
    );
    println!(
        "pending key={} mouse={}",
        hid.key_pending(),
        hid.mouse_pending()
    );
    0
}
