# Calling convention v0.1

**Related:** [plover-asm.md](plover-asm.md) · [microcode-spec.md](microcode-spec.md)

## Registers

| Reg | Role |
|-----|------|
| R0 | Argument / return value |
| R1 | Scratch |
| R2 | Result (ADD_RR) |
| R3 | Callee-saved (optional) |

## CALL / RET

- `CALL target` — push **return PC** (address after CALL) on software return stack; PC ← target (16-bit absolute).
- `RET` — pop return PC from stack.

Return stack is **software** (RAM list in VM fast/macro engines; RP @ `$F600` on target Forth layout).

## Branch

- `BEQ target` — if Z after prior CMP/SUB, PC ← 16-bit absolute target.
- `JMP target` — unconditional 16-bit absolute.

Instructions are **3 bytes**: opcode, addr_lo, addr_hi.
