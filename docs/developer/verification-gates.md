# Developer verification gates

Commands for **pre-breadboard simulation** and **software regression**. Not part of external normative specs.

## Hardware — FSM table

```bash
python tools/verify_control_store.py --v1.0
```

## Hardware — hwsim (electrical)

```bash
python -m hwsim run --all
python -m hwsim run hw/tests/alu8_full.yaml
python -m hwsim run hw/tests/cpld_seq_add.yaml
python -m hwsim run hw/tests/mem_decode_breadboard.yaml
python -m hwsim run hw/tests/cpu_cw_direct_add.yaml
```

Artifacts: `build/hwsim/<test>/`

Regenerate normative ALU timing table §3.1: `python tools/gen_alu_opcodes_timing_doc.py` (after `alu8_opcode_timing`).

See [simulation/hw-sim.md](simulation/hw-sim.md).

## Software — pytest

```bash
python -m pytest tests/ -q
```

## Software — Rust workspace

```bash
cargo test --workspace
```

## Logic VM — scenarios

```bash
cargo run -p plover_vm -- scenario hw/scenarios/vm/forth_boot.yaml
cargo run -p plover_vm -- scenario hw/scenarios/vm/boot_jmp_handoff.yaml
cargo run -p plover_vm -- scenario hw/scenarios/vm/dos_boot.yaml
cargo run -p plover_vm -- dos-shell
```

See [simulation/vm-rust.md](simulation/vm-rust.md).

## Milestone index

| Milestone | Breadboard normative | Developer pre-flight |
|-----------|----------------------|----------------------|
| M1 | [../normative/hw-bringup/M1-alu.md](../normative/hw-bringup/M1-alu.md) | `alu8_full.yaml` |
| M2a | [../normative/hw-bringup/M2a-cpld-decode.md](../normative/hw-bringup/M2a-cpld-decode.md) | `cpld_seq_add.yaml` |
| M2b | [../normative/hw-bringup/M2b-gpr-memory.md](../normative/hw-bringup/M2b-gpr-memory.md) | `mem_decode_breadboard.yaml` |
| M3 | [../normative/hw-bringup/M3a-control-store.md](../normative/hw-bringup/M3a-control-store.md) | `verify_control_store.py --v1.0` |
| M4 | [../normative/hw-bringup/M4b-boot-hardware.md](../normative/hw-bringup/M4b-boot-hardware.md) | `boot_jmp_handoff.yaml` |
| M5 | [../normative/hw-bringup/M5-cpu-e2e.md](../normative/hw-bringup/M5-cpu-e2e.md) | `hwsim run --all` |
| S0–S7 | [../normative/software/software-roadmap.md](../normative/software/software-roadmap.md) | `pytest tests/` |
