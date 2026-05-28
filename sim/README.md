# Simulation (`sim`)

Icarus Verilog testbenches and control-ROM images for the Plover simulator.

## ALU testbench

| File | Purpose |
|------|---------|
| [tb_alu8.v](tb_alu8.v) | Vector tests for [rtl/alu/alu8.v](../rtl/alu/alu8.v) |

```bash
make sim-alu
```

## Core testbench

| File | Purpose |
|------|---------|
| [tb_plover_core.v](tb_plover_core.v) | Runs [rtl/cpu/plover_core.v](../rtl/cpu/plover_core.v) with ROM loaded |
| [rom_low.hex](rom_low.hex) | Control word bits [7:0] per address |
| [rom_high.hex](rom_high.hex) | Control word bits [15:8] per address |

```bash
make rom       # from lib/inc_r1.micro
make sim-core
make test      # ALU + core
```

Default program (`lib/inc_r1.micro`): increment R1, then HALT. Expect `r1=01`, `pc=0001` after run.

### Waveforms

```bash
make sim-core
# or rebuild with VCD:
# iverilog ... && vvp -vcd sim/wave.vcd build/core.out
vvp +vcd build/core.out   # if testbench extended; current TB uses +vcd via $test$plusargs("vcd")
```

Icarus: run with `vvp +vcd` only if [tb_plover_core.v](tb_plover_core.v) is invoked with `+vcd` plusarg (see `$test$plusargs("vcd")` in the testbench).

## Working directory

Run `make` from the **repository root** so `sim/rom_*.hex` paths match [control_rom.v](../rtl/mem/control_rom.v) defaults.

## See also

- [../rtl/README.md](../rtl/README.md)  
- [../tools/README.md](../tools/README.md)  
