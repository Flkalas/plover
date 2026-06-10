# Example microprograms (`lib`)

Sample `.micro` files for the [microassembler](../tools/microasm.py). Output goes to `sim/rom_low.hex` and `sim/rom_high.hex`.

## Programs

| File | Description |
|------|-------------|
| [inc_r1.micro](inc_r1.micro) | Increment R1, halt — default `make rom` input |
| [add_r0_r1.micro](add_r0_r1.micro) | R1 ← R1 + R1 (two cycles; same-register encoding demo) |

## Assemble

```bash
python3 tools/microasm.py lib/inc_r1.micro -o sim
make sim-core
```

## Writing new programs

1. Set address with `@0000`  
2. One control word per line (`alu` \| `reg` \| `bus` \| `branch`)  
3. Assemble and run `make sim-core`  

Cross-register moves in **one** cycle are not supported by the 4-bit `reg_ctl` field; use multiple lines or memory (see spec).

## See also

- [../docs/hardware/microcode-spec.md](../docs/hardware/microcode-spec.md)  
