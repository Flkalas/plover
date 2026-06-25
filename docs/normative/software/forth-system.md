# Forth system (S3)

Host-side minimal Forth core used as the behavioral reference for later VM and normative-asm ports.

## Scope (v0.1 S3)

- Data stack primitives: `DUP DROP SWAP`
- Arithmetic: `+ - *`
- Output: `.`
- Colon definitions: `:` … `;`
- Line evaluator: `eval_line` (QUIT-like)

## Implementation

- Python reference: `forth/interpreter.py`
- Rust port: `crates/plover_forth` (`cargo test -p plover_forth`)
- Scenario kind: `kind: forth` in `hw/scenarios/vm/*.yaml`
- Runner: `python tools/run_forth_demo.py`

## Gate

- `tests/test_forth_primitives.py`
- `tests/test_forth_interpret.py`
- `tests/test_forth_normative.py` (micro engine regression guard)
- `- `
