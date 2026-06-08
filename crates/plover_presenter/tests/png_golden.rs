use plover_copro::mailbox::Mailbox;
use plover_copro::vdu::{CMD_GFX_FILLRECT, CMD_VDU_CLS, CMD_VDU_MODE, CMD_VDU_PRINT, CMD_VDU_VSYNC, MODE_BITMAP};
use plover_presenter::compose::{compose_rgb, upscale_nearest_2x, OUTPUT_H, OUTPUT_W};
use std::fs;
use std::path::PathBuf;

fn fixture_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/png")
}

fn rgb_to_png(rgb: &[u8], w: u32, h: u32) -> Vec<u8> {
    let mut out = Vec::new();
    {
        let mut enc = png::Encoder::new(&mut out, w, h);
        enc.set_color(png::ColorType::Rgb);
        enc.set_depth(png::BitDepth::Eight);
        let mut writer = enc.write_header().unwrap();
        writer.write_image_data(rgb).unwrap();
    }
    out
}

fn png_pixel_at(png_bytes: &[u8], x: u32, y: u32) -> (u8, u8, u8) {
    let decoder = png::Decoder::new(png_bytes);
    let mut reader = decoder.read_info().unwrap();
    let mut buf = vec![0u8; reader.output_buffer_size()];
    let info = reader.next_frame(&mut buf).unwrap();
    let bytes = &buf[..info.buffer_size()];
    let stride = info.width as usize * 3;
    let i = y as usize * stride + x as usize * 3;
    (bytes[i], bytes[i + 1], bytes[i + 2])
}

#[test]
fn vdu_smoke_png_golden() {
    let mut mb = Mailbox::default();
    mb.issue_vdu(CMD_VDU_MODE, MODE_BITMAP, 0, None);
    mb.issue_vdu(CMD_VDU_CLS, 0x07, 0, None);
    mb.issue_vdu(CMD_VDU_PRINT, 5, 0, Some(b"HELLO"));
    mb.issue_vdu(
        CMD_GFX_FILLRECT,
        0,
        0,
        Some(&[10, 10, 4, 4, 0x00, 0xF8]),
    );
    mb.issue_vdu(CMD_VDU_VSYNC, 0, 0, None);

    let logical = compose_rgb(&mb.vdu);
    let frame = upscale_nearest_2x(&logical);
    let png = rgb_to_png(&frame, OUTPUT_W as u32, OUTPUT_H as u32);

    let dir = fixture_dir();
    fs::create_dir_all(&dir).unwrap();
    let golden_path = dir.join("vdu_smoke.png");
    if !golden_path.is_file() {
        fs::write(&golden_path, &png).expect("write golden PNG");
    }
    let golden = fs::read(&golden_path).unwrap();
    assert_eq!(golden.len(), png.len(), "PNG size drift — review golden");
    for (i, (a, b)) in golden.iter().zip(png.iter()).enumerate() {
        assert_eq!(a, b, "PNG byte mismatch at {i}");
    }

    let (r, g, b) = png_pixel_at(&png, 20, 20);
    assert!(r > 200 && g < 30 && b < 30, "red fillrect at 2x upscale");
}
