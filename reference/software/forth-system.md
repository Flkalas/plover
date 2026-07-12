# Forth system (S3)

Host-side minimal Forth core — behavioral reference for normative asm ports.

## Scope (v0.1 S3)

- Data stack primitives: `DUP DROP SWAP`
- Arithmetic: `+ - *`
- Output: `.`
- Colon definitions: `:` … `;`
- Line evaluator: `eval_line` (QUIT-like)

## Implementation

Behavioral reference for normative asm ports. Breadboard burn uses frozen fixtures in [fixtures](../fixtures/) — no host toolchain in the Active tree.

Breadboard bring-up does **not** require Forth on the TTL CPU.
