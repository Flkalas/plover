//! Headless `play --pls media_bench.pls` gate (demo-program-spec §5.4).

use plover_core::{EngineKind, PloverMachine};
use plover_scenario::assemble_pls;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn media_bench_play_headless_frame_and_gfx() {
    let root = repo_root();
    let bytes = assemble_pls(&root, "hw/fixtures/sw/media_bench.pls", 0x00E0)
        .expect("assemble media_bench.pls");

    let mut m = PloverMachine::with_engine(EngineKind::Fast);
    m.set_map_mode(1);
    m.load_ram(&bytes, 0x00E0);
    m.set_pc(0x00E0);
    m.run(80_000);

    assert!(!m.halted(), "unexpected HALT pc={:#06x}", m.pc());
    assert!(
        m.bus.mailbox.vdu.frame >= 1,
        "expected VSYNC after init, frame={}",
        m.bus.mailbox.vdu.frame
    );
    assert_eq!(m.bus.mailbox.vdu.chars[0][0], b'P');
    assert_eq!(
        m.bus.mailbox.vdu.bitmap[20 * 320 + 10],
        0xF800,
        "fillrect red pixel @ (10,20)"
    );
}
