# Bare-metal GPIO smoke (ROM Stage1)

Stage1 verifies hardware I/O **before OS** by executing ROM-resident asm logic.

## Goal

- Read a switch bit through GPIO input
- Toggle LED output bit based on polling loop
- Use blink/error code behavior as visual execution trace

## Minimal flow

1. Set GPIO direction (`bit0-3` output, `bit4-7` input)
2. Poll switch input bit (`bit5`)
3. If pressed, set LED bit0; else clear LED bit0
4. Repeat with delay loop

## Why first

If this passes, address/data/control timing to basic I/O is proven independent of kernel/filesystem complexity.

## VM gate

- `hw/scenarios/vm/rom_gpio_smoke.yaml`
- `tests/test_rom_gpio_smoke.py`

