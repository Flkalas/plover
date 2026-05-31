# Tools

Offline utilities for microcode and ROM images (no hardware programmer required for sim).

## microasm.py

Assembles `.micro` source into 16-bit control words and writes `rom_low.hex` / `rom_high.hex`.

```bash
python3 tools/microasm.py lib/inc_r1.micro -o sim
```

Syntax: see [docs/microcode-spec.md](docs/microcode-spec.md).

Example line:

```text
alu INC | reg R1<=ALU | bus ALU_TO_REG | branch INC
```

## pack_rom.py

Pack explicit hex words into dual ROM files:

```bash
python3 tools/pack_rom.py 9310 0005 -o sim
```

## Makefile targets

| Target | Action |
|--------|--------|
| `make rom` | `microasm lib/inc_r1.micro` → `sim/` |

## See also

- [../lib/README.md](../lib/README.md) — example programs
- [../../docs/hw-sim.md](../../docs/hw-sim.md) — current electrical simulator (repo root)
