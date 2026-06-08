use crate::kernel::Kernel;
use crate::vfdd::VfddDriver;
use plover_copro::mailbox::{CMD_READ, MB_BUFFER, MB_CMD, MB_PARAM};
use plover_copro::vfdd::{VfdConfig, VirtualFdd};
use plover_mmu::MemoryBus;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct KernelScenarioResult {
    pub ok: bool,
    pub output: Vec<String>,
    pub error: Option<String>,
}

pub fn run_kernel_scenario_yaml(
    actions: &[serde_yaml::Value],
    expect: &serde_yaml::Value,
    root: &Path,
) -> KernelScenarioResult {
    let bus = MemoryBus::default();
    let mut k = Kernel::new(bus);
    for action in actions {
        let typ = action.get("type").and_then(|v| v.as_str()).unwrap_or("");
        if let Err(e) = apply_kernel_action(&mut k, action, typ, root) {
            return KernelScenarioResult {
                ok: false,
                output: k.state.output.clone(),
                error: Some(e),
            };
        }
    }
    let mut ok = true;
    if let serde_yaml::Value::Mapping(map) = expect {
        if let Some(items) = map.get(&serde_yaml::Value::String("output_contains".into())) {
            if let serde_yaml::Value::Sequence(seq) = items {
                for item in seq {
                    if let serde_yaml::Value::String(s) = item {
                        if !k.state.output.iter().any(|line| line.contains(s)) {
                            ok = false;
                        }
                    }
                }
            }
        }
    }
    KernelScenarioResult {
        ok,
        output: k.state.output,
        error: None,
    }
}

fn apply_kernel_action(
    k: &mut Kernel,
    action: &serde_yaml::Value,
    typ: &str,
    root: &Path,
) -> Result<(), String> {
    match typ {
        "stage0_load_sector0" => {
            let img_rel = action
                .get("image")
                .and_then(|v| v.as_str())
                .unwrap_or("hw/fixtures/vfdd/dos_boot.img");
            let sectors = action
                .get("sectors")
                .and_then(|v| v.as_u64())
                .unwrap_or(64) as usize;
            let path = root.join(img_rel.replace('/', std::path::MAIN_SEPARATOR_STR));
            let dev = VirtualFdd::new(VfdConfig {
                path,
                sector_count: sectors,
            })
            .map_err(|e| e.to_string())?;
            let drv = VfddDriver::new(dev);
            let sector = drv.read_sector(0).map_err(|e| format!("{e:?}"))?;
            k.bus.mailbox.set_sector_stub(&sector);
            k.bus.write_cpu(MB_PARAM, 0);
            k.bus.write_cpu(MB_CMD, CMD_READ);
            for i in 0..248 {
                let b = k.bus.read_cpu(MB_BUFFER.wrapping_add(i as u16));
                k.bus.write_cpu(0x0800u16.wrapping_add(i as u16), b);
            }
            k.kprint("bios_stage0_ok");
        }
        "stage1_gpio_smoke" => {
            let sw_on = action
                .get("switch")
                .and_then(|v| v.as_u64())
                .unwrap_or(1) as u8
                & 1;
            k.gpio.direction = 0x0F;
            k.gpio.set_input_bits(1 << 5, if sw_on != 0 { 1 << 5 } else { 0 });
            if k.gpio.get_bit(5) {
                k.gpio.set_bit(0);
                k.kprint("gpio_smoke_led_on");
            } else {
                k.gpio.clear_bit(0);
                k.kprint("gpio_smoke_led_off");
            }
        }
        "set_slots" => {
            if let Some(slots) = action.get("slots").and_then(|v| v.as_mapping()) {
                for (ks, v) in slots {
                    let slot: u8 = match ks {
                        serde_yaml::Value::String(s) => {
                            s.trim_matches('"').parse().unwrap_or(0)
                        }
                        serde_yaml::Value::Number(n) => n.as_u64().unwrap_or(0) as u8,
                        _ => 0,
                    };
                    let sig: u8 = v
                        .as_u64()
                        .or_else(|| v.as_i64().map(|i| i as u64))
                        .unwrap_or(0xFF) as u8;
                    k.state.slot_signatures.insert(slot, sig);
                }
            }
        }
        "boot" => k.boot(),
        "alloc" => {
            let _n = action.get("bytes").and_then(|v| v.as_u64()).unwrap_or(0);
        }
        other => return Err(format!("unknown kernel action: {other}")),
    }
    Ok(())
}
