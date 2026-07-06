# Calling convention v0.1

**Related:** [plover-asm.md](plover-asm.md) · [microcode-spec.md](../hardware/microcode-spec.md)

## Registers (Gi1 v1.0)

| Reg | Role |
|-----|------|
| **R0 (AC)** | Argument / return value; only **hardware** GPR in CPLD |
| **RAM cells** | Scratch, callee-saved, multi-operand temps — software convention |

Gi1 has **no** hardware R1/R2. Values that previously lived in R1/R2 use **fixed RAM slots** or stack cells per function ([software-memory-layout.md](software-memory-layout.md)).

## ADD semantics

`ADD #imm` → **R0 ← R0 + imm** (imm latched in MBR during execute). No separate result register.

## CALL / RET

- `CALL target` — push **return PC** (address after CALL) on software return stack; PC ← target (16-bit absolute).
- `RET` — pop return PC from stack.

Return stack is **software** (RAM list in VM fast/macro engines; RP @ `$F600` on target Forth layout).

## Branch

- `BEQ target` — if Z after prior CMP/SUB, PC ← 16-bit absolute target.
- `JMP target` — unconditional 16-bit absolute.

Instructions are **3 bytes**: opcode, addr_lo, addr_hi.

## Archived (rev G)

3-GPR + TFR calling patterns: [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md).
