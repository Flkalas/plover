# CPU core (`rtl/cpu`)

Top-level **1-cycle-per-microinstruction** core: fetch 16-bit control word, drive ALU/registers/bus/PC.

## Files

| File | Role |
|------|------|
| [plover_defines.vh](plover_defines.vh) | `ALU_*`, `BUS_*`, `BR_*` localparams |
| [plover_core.v](plover_core.v) | `plover_core` module |

## Cycle behavior (ideal model)

1. `cw = ROM[pc]`  
2. Decode fields → ALU, `reg_ctl`, `bus_ctl`, `branch`  
3. Combinational ALU + bus; register write on `posedge clk`  
4. Update PC / `halted` on `posedge clk`  

## Icarus notes

- Testbenches use **time delays** (`#25`) instead of `@(posedge clk)` to avoid delta-cycle stalls with large combinational paths.  
- Async reset: `rst_n` low clears PC and flags.

## Probes (for VCD / debug)

`probe_r0` … `probe_r6`, `probe_pc`, `probe_cw`, `probe_alu_y`, `probe_bus` — see testbench wiring in [sim/tb_plover_core.v](../../sim/tb_plover_core.v).

## Test

```bash
make rom       # refresh sim/rom_*.hex
make sim-core
```

## See also

- [../README.md](../README.md)  
- [../../docs/microcode-spec.md](../../docs/microcode-spec.md)  
