# Timing and clock — fit study variants

**Source baseline:** [reference/hardware/alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md) (read-only; not edited).

**Execute half-cycle budget:** \(T_{exec} = 1 / (2 f_{clk})\)

## Path model (operand and CW)

| ID | Path | max (ns) | Components |
|----|------|----------|------------|
| **P0** | CPLD `q_a/b` → ALU INC | **168** | CPLD 15 + ALU 153 |
| **P1** | 574 Q → ALU INC (A1) | **176** | 574 tCO 23 + ALU 153 |
| **P2** | P1 + breadboard wire | **186** | +10 ns derating |
| **P3** | SUB/CMP Y | **151** | CPLD 15 + ALU 136 |
| **P4** | Y → GPR 574 setup | **181** | ALU 153 + 574 setup 28 |
| **P5** | CMP → FLG | **≤179** | flags ≤151 + setup 28 |
| **P6a** | EEPROM CW → 574 latch | **98** | EEPROM t_ACC 70 + setup 28 |
| **P6b** | P6a + bus fanout | **~110** | +12 ns est. |

## Clock derivation

```
t_path     = Σ(component max) + t_wire_breadboard
T_exec_min = t_path + t_margin_setup    (margin_setup = 30 ns recommended)
f_clk_max  = 1 / (2 × T_exec_min)
```

| Scenario | t_path (ns) | +30 margin | f_clk_max | Recommended nominal |
|----------|------------:|-----------:|----------:|---------------------|
| Baseline CPLD GPR (P0) | 168 | 198 | **2.53 MHz** | **2.0 MHz** (22% slack) |
| A1 external GPR (P1) | 176 | 206 | **2.43 MHz** | **2.0 MHz** (18% slack) |
| A1 + breadboard (P2) | 186 | 216 | **2.31 MHz** | **1.5–2.0 MHz** bring-up |
| Conservative (+25% on P0) | 210 | 240 | **2.08 MHz** | **1.5 MHz** |
| D5 2-byte CW @ phase edge (2×P6b) | 220 | — | macro extend | Place CW fetch in **fetch** slot |

## Variant notes

- **Tier C / direct strobes:** ALU controls latched or stable for the phase — operand paths P0–P5 dominate `f_clk`.
- **D5 EEPROM:** P6 independent if CW load completes before execute; otherwise add macro half-cycle or lower `f_clk`.
- **OSC mapping (if adopted later):** 2.0 MHz ← 4.000 MHz ÷2; 1.5 MHz ← 3.000 MHz ÷2 or 6 MHz ÷4.

## Worst-case opcode (unchanged)

**INC** sets ALU comb limit at **153 ns**; fit-study does not change the 12-DIP ALU netlist.
