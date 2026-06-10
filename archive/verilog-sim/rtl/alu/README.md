# ALU RTL (`rtl/alu`)

8-bit arithmetic/logic unit matching the Plover BOM ALU section (12× 74HC-class ICs), modeled for simulation before breadboard wiring.

## Files

| File | Hardware | Model |
|------|----------|--------|
| [hc283_cascade.v](hc283_cascade.v) | 74HC283×2 | Two 4-bit ripple adders, `C_out` → `C_in` |
| [hc153_mux4.v](hc153_mux4.v) | 74HC153 | Dual 4:1 MUX (per nibble); **not wired into `alu8` yet** |
| [alu8.v](alu8.v) | Full ALU | Top-level: add/sub, AND/OR/XOR/NOT, pass, inc/dec |

## BOM vs simulation

| Part | In RTL |
|------|--------|
| 74HC283×2 | Yes — `hc283_cascade` |
| 74HC86 | Inline — `b ^ 8'hFF` for subtract; XOR via `^` |
| 74HC08 / 32 | Inline — `&` and `\|` |
| 74HC153×4 | **Simplified** — output mux is a Verilog `case (alu_sel)` instead of four 153s |

SUB borrow flag: `cout = ~cout_arith` (see [microcode-spec](../../docs/hardware/microcode-spec.md)).

## Interface (`alu8`)

- `a[7:0]`, `b[7:0]` — operands  
- `alu_sel[3:0]` — operation (0=NOP … 11=CMP)  
- `y[7:0]`, `cout`, `zero` — result and flags  

## Test

```bash
make sim-alu
```

Testbench: [sim/tb_alu8.v](../../sim/tb_alu8.v).

## See also

- [../README.md](../README.md) — full datapath  
- [../../docs/hardware/microcode-spec.md](../../docs/hardware/microcode-spec.md) — `alu_sel` encoding  
