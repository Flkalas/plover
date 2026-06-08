# Plover software tests

Cumulative pytest gates for the VM OS stack (S0–S7).

## Run all

```bash
pytest tests/ -q
```

## Milestone gate

```bash
python tools/run_sw_regression.py --through S4
```

## Layers

| Layer | Examples |
|-------|----------|
| L1 unit | `test_plover_asm`, `test_fat_fs` |
| L2 VM | `test_add_imm`, `test_call_ret`, `test_plr_exec` |
| L3 scenario | `hw/scenarios/vm/*.yaml` via `plover_vm scenario` |

Normative acceptance uses `--engine micro` where applicable.

## Manifest (cumulative)

| Milestone | New tests |
|-----------|-----------|
| baseline | `test_add_imm`, `test_control_store`, … |
| S1 | `test_plover_asm` |
| S2 | `test_call_ret` |
| S3 | `test_forth_primitives`, `test_forth_interpret` |
| S4 | `test_forth_blocks` |
| S5 | `test_plover_cc` |
| S6 | `test_kernel_boot`, `test_boot_jmp_handoff`, `test_boot_handoff` |
| S7a–d | `test_vfdd_io`, `test_fat_fs`, `test_plr_exec`, `dos_boot.yaml` |

Tests are never removed; only extended.
