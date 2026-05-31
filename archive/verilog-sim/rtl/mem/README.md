# Memory (`rtl/mem`)

Models **SST39SF010A×2** (control ROM) and **IS62C256** (SRAM).

## Files

| File | Hardware | Notes |
|------|----------|--------|
| [control_rom.v](control_rom.v) | 2× 8-bit flash in parallel | 16-bit control word per address; `$readmemh` from `sim/rom_low.hex` + `sim/rom_high.hex` |
| [sram256.v](sram256.v) | IS62C256 32K×8 | **Sim depth = 256 bytes** (not full 32K — faster Icarus runs) |

## Control ROM

- `cw[15:0] = { rom_hi[addr], rom_lo[addr] }`  
- Default `DEPTH = 2` in core (size to your program; increase parameter if needed)  
- Paths are relative to simulation working directory (repo root when using `make`).

## SRAM

- Address from core: `{ R1, R0 }` (16-bit), uses `addr[14:0]`  
- Combinational read, synchronous write on `posedge clk`  

## See also

- [../../tools/microasm.py](../../tools/microasm.py) — generate ROM hex  
- [../../docs/microcode-spec.md](../../docs/microcode-spec.md)  
