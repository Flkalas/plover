# RTL — Plover Verilog models

Ideal (zero-delay) behavioral models of the discrete 74HC datapath described in the root [README](../README.md) and [BOM](../BOM.md). Target simulator: **Icarus Verilog**.

## Block diagram

```
PC → control_rom (16b CW) → plover_core
                              ├─ regfile (7× 574)
                              ├─ databus
                              ├─ alu8
                              └─ sram256
```

## Subdirectories

| Folder | BOM | README |
|--------|-----|--------|
| [alu/](alu/) | 74HC283×2, 153×4, 86/08/32 | [alu/README.md](alu/README.md) |
| [reg/](reg/) | 74HC574×7 | [reg/README.md](reg/README.md) |
| [bus/](bus/) | 74HC157, 245 | [bus/README.md](bus/README.md) |
| [mem/](mem/) | SST39SF010A×2, IS62C256 | [mem/README.md](mem/README.md) |
| [cpu/](cpu/) | 74HC161 (PC), integration | [cpu/README.md](cpu/README.md) |

## Build / test

From repository root (WSL or Linux recommended):

```bash
make sim-alu    # ALU only
make sim-core   # full core (builds ROM via make rom)
make test       # both
```

## Conventions

- `` `default_nettype none `` on combinational modules
- Control word definition: [docs/hardware/microcode-spec.md](../docs/hardware/microcode-spec.md)
- Simulation ROM images: [sim/rom_*.hex](../sim/)
