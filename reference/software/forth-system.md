# Forth system (S3)

Host-side minimal Forth core — behavioral reference for normative asm ports.

## Scope (v0.1 S3)

- Data stack primitives: `DUP DROP SWAP`
- Arithmetic: `+ - *`
- Output: `.`
- Colon definitions: `:` … `;`
- Line evaluator: `eval_line` (QUIT-like)

## Implementation (archived)

Reference interpreter and Rust port are in archived bundles (`host_toolchain.tar.gz`, `rust_vm.tar.gz`). See [archived-code-guide.md](../../archive/MANIFEST.md).

Breadboard bring-up does **not** require Forth on the TTL CPU.
