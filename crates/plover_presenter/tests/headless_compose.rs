use plover_copro::mailbox::Mailbox;
use plover_copro::vdu::{CMD_GFX_FILLRECT, CMD_VDU_MODE, CMD_VDU_VSYNC, MODE_BITMAP};
use plover_presenter::compose::{compose_rgb, upscale_nearest_2x, LOGICAL_H, LOGICAL_W, OUTPUT_H, OUTPUT_W};
use plover_presenter::HeadlessPresenter;

#[test]
fn compose_fillrect_red_pixel() {
    let mut mb = Mailbox::default();
    mb.issue_vdu(CMD_VDU_MODE, MODE_BITMAP, 0, None);
    mb.issue_vdu(
        CMD_GFX_FILLRECT,
        0,
        0,
        Some(&[10, 10, 4, 4, 0x00, 0xF8]),
    );
    mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);

    let logical = compose_rgb(&mb.vdu);
    assert_eq!(logical.len(), LOGICAL_W * LOGICAL_H * 3);
    let idx = (10 * LOGICAL_W + 10) * 3;
    assert!(logical[idx] > 200);
    assert!(logical[idx + 1] < 20);
    assert!(logical[idx + 2] < 20);

    let scaled = upscale_nearest_2x(&logical);
    assert_eq!(scaled.len(), OUTPUT_W * OUTPUT_H * 3);
}

#[test]
fn headless_temporal_hold() {
    let mut mb = Mailbox::default();
    let mut pres = HeadlessPresenter::default();
    assert!(!pres.tick(&mb.vdu));
    mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);
    assert!(pres.tick(&mb.vdu));
    assert_eq!(pres.pixels().len(), OUTPUT_W * OUTPUT_H * 3);
}
