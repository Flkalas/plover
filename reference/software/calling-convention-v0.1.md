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

- `CALL target` — opcode pushes **return PC** (address after the 3-byte insn) on the software return stack; PC ← target (16-bit absolute).
- `RET` — opcode pops return PC from stack into PC.

**Hardware:** push/pop performed by **CPLD-CU @ macro_end** ([microcode-spec.md](../hardware/microcode-spec.md) §2.3) — not separate LDA/STA opcodes.

| Cell | Role |
|------|------|
| `$0F00` / `$0F01` | **RP** — stack pointer (16-bit LE) |
| `$F600`–`$FEEF` | Return-address stack body (upward growth) |

Boot initial RP = `$F600` ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md), [software-memory-layout.md](software-memory-layout.md)).

## Branch

- `BEQ target` — if Z after prior CMP/SUB, PC ← 16-bit absolute target.
- `JMP target` — unconditional 16-bit absolute.

Instructions are **3 bytes**: opcode, addr_lo, addr_hi.

## Archived (rev G)

3-GPR + TFR calling patterns: [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md).
