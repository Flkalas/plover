# OS kernel (S6)

Host-side microkernel model used for early bring-up on `plover_vm`.

## Responsibilities

- Boot flow and shell entry point
- Minimal bump allocator (`kmalloc`)
- Console output (`kprint`)

## Implementation

- Kernel model: `kern/kernel.py`
- Scenario kind: `kind: kernel` in `hw/scenarios/vm/os_boot.yaml`

## Gate

- `tests/test_kernel_boot.py`
- `python -m plover_vm scenario hw/scenarios/vm/os_boot.yaml`

