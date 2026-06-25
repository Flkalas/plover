# Plover — developer documentation

**Audience:** repository contributors — simulation, VM, pytest, implementation tracking.

External learners and reviewers should use [../normative/README.md](../normative/README.md) instead.

## Quick start

| Tool | Doc |
|------|-----|
| Electrical sim (`hwsim`) | [simulation/hw-sim.md](simulation/hw-sim.md) |
| Logic VM (`plover_vm`) | [simulation/vm-rust.md](simulation/vm-rust.md) |
| Verification gates | [verification-gates.md](verification-gates.md) |

```bash
python -m hwsim run --all
cargo run -p plover_vm -- scenario hw/scenarios/vm/forth_boot.yaml
python -m pytest tests/ -q
```

## Project tracking

| Document | Description |
|----------|-------------|
| [project/implementation-plan-v1.0.md](project/implementation-plan-v1.0.md) | M1–M5 + S0–S7 status |
| [project/roadmap-next.md](project/roadmap-next.md) | Near-term tasks |
| [project/bom-maintenance.md](project/bom-maintenance.md) | BOM history / reconciliation |
| [software/demo-program-spec.md](software/demo-program-spec.md) | Demo / workshop programs |
