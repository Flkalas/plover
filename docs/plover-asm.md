# Plover assembler (S1)

**Package:** `plover_asm/` · **CLI:** `python -m plover_asm build hw/fixtures/sw/*.asm -o hw/fixtures/sram/`

## Syntax

- Labels: `name:` (absolute address)
- Directives: `.ORG addr`, `.EQU name value`, `.DB n`, `.DW addr16`
- Comments: `; ...`

## Opcodes (normative)

| Mnemonic | Bytes | Operand |
|----------|-------|---------|
| ADD | 2 | imm8 |
| LDA, STA, LDIO, STIO, CMP | 2 | addr8 |
| BEQ, JMP, CALL | 3 | addr16 LE |
| RET, HALT, ADD_RR | 1 | — |

Branch targets use **absolute** 16-bit addresses (label or `$hex`).

## Example

```asm
        .ORG 0
start:  ADD 5
        ADD 3
        HALT
```

## Output

- `.sram.hex` — byte image
- `.lst` — listing
- `.map` — symbol table
