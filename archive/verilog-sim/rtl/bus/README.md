# Bus (`rtl/bus`)

Models **74HC157 / 74HC245** style data-bus arbitration in a simplified single-driver mux.

## Files

| File | Role |
|------|------|
| [databus.v](databus.v) | Select among ALU output, register read data, or SRAM read data |

## Signals

| Input | When active |
|-------|-------------|
| `drv_alu` | Drive bus from `alu_out` (e.g. `BUS_ALU_TO_REG`) |
| `drv_reg` | Drive bus from `reg_out` (reserved; currently unused in core) |
| `drv_mem` | Drive bus from `mem_out` (`BUS_MEM_READ`) |

Only one driver may be active per cycle. Multiple drivers are a programming error (not checked at runtime in current RTL).

## BOM note

Full hardware uses 74HC157 for address mux and 74HC245 for tri-state isolation; this module only covers the **8-bit data bus** merge used in the simulator MVP.

## See also

- [../cpu/plover_core.v](../cpu/plover_core.v)  
