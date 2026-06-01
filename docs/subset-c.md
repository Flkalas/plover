# Subset C (S5)

The v0.1 Subset-C compiler is a **bootstrap tool** used to generate small Plover programs.
It is intentionally tiny and grows only as needed for kernel bring-up.

## Supported (v0.1)

- `int main(void) { return <int>; }`
- `int main(void) { return add(<int>, <int>); }` (built-in `add` pattern)

## Output

- Subset C → Plover asm text → `plover_asm` → `.sram.hex`

## CLI

```bash
python -m plover_cc hw/fixtures/sw/cc_smoke.c -o hw/fixtures/sram/cc_smoke.sram.hex
```

## Tests

- `tests/test_plover_cc.py`

