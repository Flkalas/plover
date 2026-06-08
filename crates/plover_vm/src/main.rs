mod demo;

use clap::{Parser, Subcommand};
use plover_core::{EngineKind, PloverMachine};
use plover_presenter::HeadlessPresenter;
use plover_scenario::{assemble_pls, repo_root_from_manifest, run_scenario_file};
use std::path::PathBuf;
#[cfg(feature = "audio")]
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
#[cfg(feature = "sdl")]
use std::thread;

#[derive(Parser)]
#[command(name = "plover_vm", about = "Plover logic VM (Rust)")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run a SRAM hex program to completion or max steps
    Run {
        program: Option<PathBuf>,
        #[arg(long)]
        nor: Option<PathBuf>,
        #[arg(long)]
        cw: Option<PathBuf>,
        #[arg(long, default_value = "boot")]
        map: String,
        #[arg(long, default_value = "fast")]
        engine: String,
        #[arg(long, default_value_t = 10_000)]
        max_steps: usize,
        #[arg(long)]
        trace: Option<PathBuf>,
        #[arg(long, default_value_t = true)]
        reset: bool,
        #[arg(long)]
        allow_running: bool,
    },
    /// Single CPU step (JSON state in/out)
    Step {
        #[arg(long)]
        state: Option<PathBuf>,
        #[arg(long, default_value = "micro")]
        engine: String,
    },
    /// Run a YAML scenario (vdu/apu/hid)
    Scenario {
        scenario: PathBuf,
    },
    /// Interactive PL-DOS shell (PLFS + .PLR)
    DosShell {
        #[arg(long, default_value = "dos_boot.img")]
        image_name: String,
    },
    /// VDU text + GFX smoke on host
    VduDemo,
    /// APU PSG ch0 tone smoke on host
    ApuDemo,
    /// HID keyboard/mouse queue smoke on host
    HidDemo,
    /// Integrated VM with Presenter (headless or SDL)
    Play {
        #[arg(long)]
        pls: PathBuf,
        #[arg(long, default_value = "0x00E0")]
        origin: String,
        #[arg(long, default_value_t = 50_000)]
        max_steps: usize,
        #[arg(long)]
        headless: bool,
        #[arg(long)]
        audio: bool,
    },
}

fn parse_origin(s: &str) -> u16 {
    let t = s.trim();
    if let Some(hex) = t.strip_prefix("0x").or_else(|| t.strip_prefix("0X")) {
        u16::from_str_radix(hex, 16).unwrap_or(0x00E0)
    } else {
        t.parse().unwrap_or(0x00E0)
    }
}

fn load_pls(m: &mut PloverMachine, root: &PathBuf, pls: &PathBuf, origin: u16) -> Result<(), String> {
    let path = if pls.is_absolute() {
        pls.clone()
    } else {
        root.join(pls)
    };
    let rel = path
        .strip_prefix(root)
        .unwrap_or(path.as_path())
        .to_string_lossy()
        .replace('\\', "/");
    let bytes = assemble_pls(root, &rel, origin)?;
    m.load_ram(&bytes, origin);
    m.set_pc(origin);
    Ok(())
}

fn cmd_run(args: &Commands) -> i32 {
    let Commands::Run {
        program,
        nor,
        cw,
        map,
        engine,
        max_steps,
        trace,
        reset,
        allow_running,
    } = args
    else {
        unreachable!();
    };
    let root = repo_root_from_manifest();
    let mut m = PloverMachine::with_engine(EngineKind::parse(engine));
    if let Some(n) = nor {
        let path = if n.is_absolute() { n.clone() } else { root.join(n) };
        m.load_nor(&path, 0);
        let vec = root.join("hw/fixtures/boot/boot_vector.hex");
        if vec.is_file() {
            m.load_nor(&vec, 0xFFFC);
        }
    } else {
        m.load_default_boot_fixtures(&root);
    }
    if let Some(c) = cw {
        let path = if c.is_absolute() { c.clone() } else { root.join(c) };
        m.load_cw(&path);
    } else if nor.is_none() {
        let cw_path = root.join("hw/fixtures/control/cw.hex");
        if cw_path.is_file() {
            m.load_cw(&cw_path);
        }
    }
    let map_mode = if map == "boot" { 0 } else { 1 };
    m.set_map_mode(map_mode);
    if let Some(prog) = program {
        let base = if map == "run" { 0x0800 } else { 0 };
        let path = if prog.is_absolute() {
            prog.clone()
        } else {
            root.join(prog)
        };
        m.load_ram_program(&path, base);
        m.set_pc(base);
    }
    if *reset {
        m.reset(Some(map_mode));
    }
    m.run(*max_steps);
    let snap = m.snapshot();
    if let Some(t) = trace {
        if let Err(e) = m.tracer.write_jsonl(t) {
            eprintln!("trace write: {e}");
            return 1;
        }
    }
    let out = serde_json::json!({
        "pc": snap.pc,
        "regs": snap.regs,
        "halted": snap.halted,
        "map_mode": snap.map_mode,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap_or_default());
    if snap.halted || *allow_running {
        0
    } else {
        0
    }
}

fn cmd_step(args: &Commands) -> i32 {
    let Commands::Step { state, engine } = args else {
        unreachable!();
    };
    let mut m = PloverMachine::with_engine(EngineKind::parse(engine));
    if let Some(path) = state {
        let text = match std::fs::read_to_string(path) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("state read: {e}");
                return 1;
            }
        };
        let v: serde_json::Value = match serde_json::from_str(&text) {
            Ok(j) => j,
            Err(e) => {
                eprintln!("state json: {e}");
                return 1;
            }
        };
        if let Some(mm) = v.get("map_mode").and_then(|x| x.as_u64()) {
            m.set_map_mode(mm as u8);
        }
        if let Some(pc) = v.get("pc").and_then(|x| x.as_u64()) {
            m.set_pc(pc as u16);
        }
        if let Some(regs) = v.get("regs").and_then(|x| x.as_array()) {
            let mut r = [0u8; 4];
            for (i, item) in regs.iter().take(4).enumerate() {
                r[i] = item.as_u64().unwrap_or(0) as u8;
            }
            m.set_regs(r);
        }
    }
    m.step_once();
    let snap = m.snapshot();
    let out = serde_json::json!({
        "pc": snap.pc,
        "regs": snap.regs,
        "halted": snap.halted,
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap_or_default());
    0
}

fn cmd_dos_shell(args: &Commands) -> i32 {
    let Commands::DosShell { image_name } = args else {
        unreachable!();
    };
    let root = repo_root_from_manifest();
    let mut rt = match plover_os::prepare_runtime(&root, image_name) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("prepare: {e}");
            return 1;
        }
    };
    rt.stage1_boot();
    rt.stage2_shell_start();
    for line in &rt.output {
        if line != &rt.prompt {
            println!("{line}");
        }
    }
    rt.output.clear();

    use std::io::{self, BufRead, Write};
    let stdin = io::stdin();
    let mut stdin = stdin.lock();
    loop {
        print!("{} ", rt.prompt);
        let _ = io::stdout().flush();
        let mut line = String::new();
        match stdin.read_line(&mut line) {
            Ok(0) | Err(_) => break,
            Ok(_) => {}
        }
        let trimmed = line.trim_end_matches(['\r', '\n']).to_string();
        let out = rt.run_command(&trimmed);
        for item in &out {
            if item != &rt.prompt {
                println!("{item}");
            }
        }
        if trimmed.eq_ignore_ascii_case("exit") {
            break;
        }
    }
    0
}

fn cmd_scenario(args: &Commands) -> i32 {
    let Commands::Scenario { scenario } = args else {
        unreachable!();
    };
    let root = repo_root_from_manifest();
    let path = if scenario.is_absolute() {
        scenario.clone()
    } else {
        root.join(scenario)
    };
    let res = run_scenario_file(&path, &root);
    if let Some(err) = &res.error {
        eprintln!("error: {err}");
        return 1;
    }
    for line in &res.output {
        eprintln!("{line}");
    }
    if res.ok {
        println!("OK");
        0
    } else {
        eprintln!("FAIL");
        1
    }
}

fn cmd_play(args: &Commands) -> i32 {
    let Commands::Play {
        pls,
        origin,
        max_steps,
        headless,
        audio,
    } = args
    else {
        unreachable!();
    };
    let root = repo_root_from_manifest();
    let origin = parse_origin(origin);
    let mut m = PloverMachine::with_engine(EngineKind::Fast);
    m.set_map_mode(1);
    if let Err(e) = load_pls(&mut m, &root, pls, origin) {
        eprintln!("load pls: {e}");
        return 1;
    }

    let ci = std::env::var("CI").is_ok();
    let use_headless = *headless || ci;

    #[cfg(feature = "audio")]
    let _audio_out = if *audio {
        let apu = Arc::new(Mutex::new(m.bus.mailbox.apu.clone()));
        match plover_presenter::AudioBridge::start(apu) {
            Ok(a) => Some(a),
            Err(e) => {
                eprintln!("audio disabled: {e}");
                None
            }
        }
    } else {
        None
    };
    #[cfg(not(feature = "audio"))]
    if *audio {
        eprintln!("audio requires --features audio");
    }

    #[cfg(feature = "sdl")]
    if !use_headless {
        return play_sdl(&mut m, *max_steps);
    }

    let _ = use_headless;
    play_headless(&mut m, *max_steps)
}

fn play_headless(m: &mut PloverMachine, max_steps: usize) -> i32 {
    let mut presenter = HeadlessPresenter::default();
    let frame_dt = Duration::from_millis(16);
    let mut next_frame = Instant::now();
    let mut steps = 0usize;

    while steps < max_steps && !m.halted() {
        m.run(100);
        steps += 100;
        if Instant::now() >= next_frame {
            presenter.tick(&m.bus.mailbox.vdu);
            next_frame += frame_dt;
        }
    }

    let vdu = &m.bus.mailbox.vdu;
    println!(
        "halted={} pc=0x{:04X} frame={} regs={:?}",
        m.halted(),
        m.pc(),
        vdu.frame,
        m.regs()
    );
    if presenter.pixels().len() == 640 * 480 * 3 {
        println!("presenter: 640x480 RGB ok");
    }
    0
}

#[cfg(feature = "sdl")]
fn play_sdl(m: &mut PloverMachine, max_steps: usize) -> i32 {
    use plover_presenter::sdl_window::SdlPresenter;

    let mut presenter = match SdlPresenter::new("Plover VM") {
        Ok(p) => p,
        Err(e) => {
            eprintln!("SDL init failed: {e}");
            return play_headless(m, max_steps);
        }
    };

    let frame_dt = Duration::from_millis(16);
    let mut next_frame = Instant::now();
    let mut steps = 0usize;

    while steps < max_steps && !m.halted() {
        if presenter.pump_events(&mut m.bus.mailbox) {
            break;
        }
        m.run(100);
        steps += 100;
        if Instant::now() >= next_frame {
            let _ = presenter.present(&m.bus.mailbox.vdu);
            next_frame += frame_dt;
            thread::sleep(Duration::from_millis(1));
        }
    }
    0
}

fn main() {
    let cli = Cli::parse();
    let code = match &cli.cmd {
        Commands::Run { .. } => cmd_run(&cli.cmd),
        Commands::Step { .. } => cmd_step(&cli.cmd),
        Commands::Scenario { .. } => cmd_scenario(&cli.cmd),
        Commands::DosShell { .. } => cmd_dos_shell(&cli.cmd),
        Commands::VduDemo => {
            let root = repo_root_from_manifest();
            demo::cmd_vdu_demo(&root)
        }
        Commands::ApuDemo => {
            let root = repo_root_from_manifest();
            demo::cmd_apu_demo(&root)
        }
        Commands::HidDemo => {
            let root = repo_root_from_manifest();
            demo::cmd_hid_demo(&root)
        }
        Commands::Play { .. } => cmd_play(&cli.cmd),
    };
    std::process::exit(code);
}
