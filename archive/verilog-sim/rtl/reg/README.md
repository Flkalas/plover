# Register file (`rtl/reg`)

Models **74HC574×7** as an 8-bit register bank (R0–R6).

## Files

| File | Role |
|------|------|
| [hc574.v](hc574.v) | Single 8-bit register, clocked write |
| [regfile.v](regfile.v) | Seven `hc574` instances, one read port + one write port per cycle |

## Register map (simulation)

| Index | Name | Typical use |
|-------|------|-------------|
| 0 | R0 | General / address low |
| 1 | R1 | General / address high |
| 2–4 | R2–R4 | General |
| 5 | R5 | Accumulator |
| 6 | R6 | Temp |

Encoding in the control word: [docs/hardware/microcode-spec.md](../../docs/hardware/microcode-spec.md) (`reg_ctl`).

## Behavior

- **Read:** `rd_data = q[rd_idx]` (combinational, pre-clock value)  
- **Write:** on `posedge clk` when `wr_en && wr_idx == i`  

Same-cycle read-modify-write on one register is supported (used for `INC R1`).

## See also

- [../cpu/plover_core.v](../cpu/plover_core.v) — connects regfile to ALU and bus  
